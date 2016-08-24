/**
 *  Search page management
 *  Args:
 *     textForm: the form containing the text input, if any
 *     fileForm: the form containing the file input, if any
 *     messageElem: the element that should display search messages
 */
var SearchFormController = function(textForm, fileForm, messageElem)

{
    this.textForm = textForm;
    this.fileForm = fileForm;
    this.messageElem = messageElem;

    // List of hashes to check against files being processed
    this.hashed_already = {
        'sha1': {},
        'sha256': {},
        'sha1_git': {}
    };
    this.algos = ['sha1', 'sha256', 'sha1_git'];
    this.CHECKSUM_RE = /^([0-9a-f]{40}|[0-9a-f]{64})$/i;
    var self = this;

    /**
     *  Show search messages on the page
     *  Args:
     *    msg: the message to show
     */
    this.searchMessage = function(msg) {
        self.messageElem.empty();
        self.messageElem.text(msg);
    };

    /**
     *  Setup the text field 
     *  Args:
     *    textFormInput: the text form's input
     */
    this.setupTextForm = function(textFormInput) {
        self.textForm.submit(function(event) {
            var q = textFormInput.val();
            if (!q) {
                event.preventDefault();
                self.searchMessage("Please enter a SHA-1 or SHA-256 checksum.");
            }
            else if (q && !q.match(self.CHECKSUM_RE)) {
                event.preventDefault();
                self.searchMessage("Invalid SHA-1 or SHA-256 checksum");
            }
        });
    };

    /** 
     *  Setup the file drag&drop UI and hashing support.
     *  Args:
     *    fileDropElem: the element receptive to drag & drop
     *    hashedListerElem: the element that receives the hased file descriptions
     *    fileFormInput: the input that actually receives files
     *    clearButton: the button used to clear currently hashed files
     */
    this.setupFileForm = function(fileDropElem, hashedListerElem, fileFormInput, clearButton) {
        if (!FileReader || !CryptoJS) {
            self.searchMessage("Client-side file hashing is not available for your browser.");
            return;
        }
        
        // Enable clicking on the text element for file picker
        fileDropElem.click(function(event) {
            event.preventDefault();
            fileFormInput.click();
        });
        
        // Enable drag&drop
        var makeDroppable = function(fileReceptionElt) {
            var fileshovering = false;

            fileReceptionElt.on('dragover', function(event) {
                event.stopPropagation();
                event.preventDefault();
            });

            fileReceptionElt.on('dragenter', function(event) {
                event.stopPropagation();
                event.preventDefault();
                if (!fileshovering) {
                    fileReceptionElt.css("border-style", "solid");
                    fileReceptionElt.css("box-shadow", "inset 0 3px 4px");
                    fileshovering = true;
                }
            });

            fileReceptionElt.on('dragover', function(event) {
                event.stopPropagation();
                event.preventDefault();
                if (!fileshovering) {
                    fileReceptionElt.css("border-style", "solid");
                    fileReceptionElt.css("box-shadow", "inset 0 3px 4px");
                    fileshovering = true;
                }
            });

            fileReceptionElt.on('dragleave', function(event) {
                event.stopPropagation();
                event.preventDefault();
                if (fileshovering) {
                    fileReceptionElt.css("border-style", "dashed");
                    fileReceptionElt.css("box-shadow", "none");
                    fileshovering = false;
                }
            });

            fileReceptionElt.on('drop', function(event) {
                event.stopPropagation();
                event.preventDefault();
                if (fileshovering) {
                    fileReceptionElt.css("border-style", "dashed");
                    fileReceptionElt.css("box-shadow", "none");
                    fileshovering = false;
                }
                var myfiles = event.originalEvent.dataTransfer.files;
                readAndHash(myfiles);
            });
        };
        makeDroppable(fileDropElem);
        
        // Connect input change and rehash
        var makeInputChange = function(fileInput) {
            return fileInput.each(function() {
                $(this).on('change', function(){
                    readAndHash(this.files);
                });
            });
        };
        makeInputChange(fileFormInput);
        
        // Connect clear button
        var makeClearButton = function(button) {
            return button.each(function() {
                $(this).click(function(event) {
                    event.preventDefault();
                    hashedListerElem.empty();
                    self.fileForm.children('.search-hidden').remove();
                    self.hashed_already = {
                        'sha1': {},
                        'sha256': {},
                        'sha1_git': {}
                    };
                });
            });
        };
        makeClearButton(clearButton);

        var readAndHash = function(filelist) {
            for (var file_idx = 0; file_idx < filelist.length; file_idx++) {
                var file = filelist.item(file_idx);
                var fr = new FileReader();
                bindReader(fr, file.name);
                fr.readAsArrayBuffer(file);
            }
        };

        var bindReader = function(freader, fname) {
            freader.onloadend = function(event) {
                if (event.target.readyState == FileReader.DONE)
                    return dedupAndAdd(event.target.result, fname);
                else
                    return null;
            };
        };

        /**
         *  Hash the buffer with SHA-1, SHA-1_GIT, SHA-256
         *  Args:
         *     buffer: the buffer to hash
         *     fname: the file name corresponding to the buffer
         *  Returns:
         *     a dict of algo_hash: hash
         */
        var hashBuffer = function (buffer, fname) {
            function str2ab(header) {
                var buf = new ArrayBuffer(header.length);
                var view = new Uint8Array(buf); // byte view, all we need is ASCII
                for (var idx = 0, len=header.length; idx < len; idx++)
                    view[idx] = header.charCodeAt(idx);
                return buf;
            }

            var content_array = CryptoJS.lib.WordArray.create(buffer);
            var git_hd_str = 'blob ' + buffer.byteLength + '\0';
            var git_hd_buffer = str2ab(git_hd_str);
            var git_hd_array = CryptoJS.lib.WordArray.create(git_hd_buffer);

            var sha1 = CryptoJS.SHA1(content_array);
            var sha256 = CryptoJS.SHA256(content_array);
            var sha1_git = CryptoJS.SHA1(git_hd_array.concat(content_array));
            return {
                'sha1': sha1 + '',
                'sha256': sha256 + '',
                'sha1_git': sha1_git + ''
            };
        };

        /**
         *  Hash the buffer and add it to the form if it is unique
         *  If not, display which file has the same content
         *  Args:
         *     buffer: the buffer to hash
         *     fname: the file name corresponding to the buffer
         */ 
        var dedupAndAdd = function(buffer, fname) {
            var hashes = hashBuffer(buffer);
            var has_duplicate = false;
            for (var algo_s in hashes) {
                if (self.hashed_already[algo_s][hashes[algo_s]] != undefined) {
                    // Duplicate content -- fileLister addition only, as duplicate
                    hashedListerElem.append($('<div>')
                                            .addClass('span3')
                                            .text(fname + ': duplicate of ' + self.hashed_already[algo_s][hashes[algo_s]]));
                    has_duplicate = true;
                    break;
                }
            }
            // First file read with this content -- fileLister and form addition
            if (!has_duplicate) {
                // Add to hashed list
                for (var algo_c in self.hashed_already)
                    self.hashed_already[algo_c][hashes[algo_c]] = fname;
                hashedListerElem.append($('<div>')
                                        .addClass('span3')
                                        .text(fname));
                var hashstring = JSON.stringify(hashes).replace('\"', '\'');
                self.fileForm.append($("<input>", {type: 'hidden',
                                                   class: 'search-hidden',
                                                   name: fname,
                                                   value: hashes['sha1']}// hashstring}
                                      ));

            }
        };
    };
};

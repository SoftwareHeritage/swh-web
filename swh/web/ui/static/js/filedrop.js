/**
 *  Search page management
 */


$.fn.extend({
    /**
     *  Call on any HTMLElement to make that element the recipient of files
     *  drag & dropped into it.
     *  Files then have their sha1 checksum calculated
     *  and searched in SWH.
     *  Args:
     *     resultDiv: the table where the result should be displayed
     *     errorDiv: the element where the error message should be displayed
     */
    filedrop: function(fileLister, searchForm) {

        return this.each(function() {

            var dragwin = $(this);
            var fileshovering = false;

            dragwin.on('dragover', function(event) {
                event.stopPropagation();
                event.preventDefault();
            });

            dragwin.on('dragenter', function(event) {
                event.stopPropagation();
                event.preventDefault();
                if (!fileshovering) {
                    dragwin.css("border-style", "solid");
                    dragwin.css("box-shadow", "inset 0 3px 4px");
                    fileshovering = true;
                }
            });

            dragwin.on('dragover', function(event) {
                event.stopPropagation();
                event.preventDefault();
                if (!fileshovering) {
                    dragwin.css("border-style", "solid");
                    dragwin.css("box-shadow", "inset 0 3px 4px");
                    fileshovering = true;
                }
            });

            dragwin.on('dragleave', function(event) {
                event.stopPropagation();
                event.preventDefault();
                if (fileshovering) {
                    dragwin.css("border-style", "dashed");
                    dragwin.css("box-shadow", "none");
                    fileshovering = false;
                }
            });
	    
            dragwin.on('drop', function(event) {
                event.stopPropagation();
                event.preventDefault();
                if (fileshovering) {
                    dragwin.css("border-style", "dashed");
                    dragwin.css("box-shadow", "none");
                    fileshovering = false;
                }
                var myfiles = event.originalEvent.dataTransfer.files;
                if (myfiles.length >= 1) {
                    handleFiles(myfiles, fileLister, searchForm);
                }
            });
        });
    },
    /**
     *  Call on a jQuery-selected input to make it sensitive to
     *  the reception of new files, and have it process received
     *  files.
     *  Args:
     *     fileLister: the element keeping track of the files
     *     searchForm: the form whose submission will POST the file
     *                 information
     */
    filedialog: function(fileLister, searchForm) {
        return this.each(function() {
            var elem = $(this);
            elem.on('change', function(){
                handleFiles(this.files, fileLister, searchForm);
            });
        });
    },
    /**
     *  Call on a jQuery-selected element to delegate its click
     *  event to the given input instead.
     *  Args:
     *     input: the element to be clicked when the caller is clicked.
     */
    inputclick: function(input) {
        return this.each(function() {
            $(this).click(function(event) {
                event.preventDefault();
                input.click();
            });
        });
    },
    /**
     *  Call on a form to intercept its submmission event and 
     *  check the validity of the text input if present before submitting
     *  the form.
     *  Args:
     *     textInput: the input to validate
     *     messageElement: the element where the warning will be written
     *     searchForm: the form that will be submitted
     */
    checkSubmission: function(textInput, messageElement) {
	var CHECKSUM_RE = /^([0-9a-f]{40}|[0-9a-f]{64})$/i;
	$(this).submit(function(event) {
	    event.preventDefault();
	    var q = textInput.val();
	    if (q && !q.match(CHECKSUM_RE)) {
		messageElement.empty();
		messageElement.html('Please enter a valid SHA-1');
	    } else {
		searchForm.submit();
	    }
	});
    }
});


var nameList = []; /** Avoid adding the same file twice      **/

/** 
 *  Start reading the supplied files to hash them and add them to the form,
 *  and add  their names to the file lister pre-search.
 *  Args:
 *     myfiles: the file array
 *     fileLister: the element that will receive the file names
 *     searchForm: the form to which we add hidden inputs with the 
 *     correct values
 */
function handleFiles(myfiles, fileLister, searchForm) {
    for (var i = 0; i < myfiles.length; i++) {
        var file = myfiles.item(i);
        if (nameList.indexOf(file.name) == -1) {
            nameList.push(file.name);
            var fr = new FileReader();
            fileLister.append(make_row(file.name));
            bind_reader(fr, file.name, searchForm);
            fr.readAsArrayBuffer(file);
        }
    }
};

/**
 *  Bind a given FileReader to hash the file contents when the file
 *  has been read
 *  Args:
 *     filereader: the FileReader object
 *     filename: the name of the file being read by the FileReader
 *     searchForm: the form the corresponding hidden input will be
 *     appended to
 */
function bind_reader(filereader, filename, searchForm) {
    filereader.onloadend = function(evt) {
        if (evt.target.readyState == FileReader.DONE){
            return fileReadDone(evt.target.result, filename, searchForm);
        }
    };
}

function make_row(name) {
    return "<div class='span3'>"+name+"</div>";
}

/**
 *  Hash the buffer contents with CryptoJS's SHA1 implementation, and
 *  append the result to the given form for submission.
 *  Args:
 *     buffer: the buffer to be hashed
 *     fname: the file name corresponding to the buffer
 *     searchForm: the form the inputs should be appended to
 */
function fileReadDone(buffer, fname, searchForm) {
    var wordArray = CryptoJS.lib.WordArray.create(buffer);
    var sha1 = CryptoJS.SHA1(wordArray);
    /**
    var git_hd = "blob " + wordArray.length + "\0";
    var git_Array = CryptoJS.enc.utf8.parse(git_hd).concat(wordArray);
    var sha256 = CryptoJS.SHA256(wordArray);
    var sha1_git = CryptoJS.SHA1(wordArray);
    **/
    searchForm.append($("<input>", {type: "hidden",
                                    name: fname,
                                    value: sha1}
                       ));
}

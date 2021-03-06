TList = Class(TObject)
Private
  Some: String;
Public
  Procedure Inside; // Suxx
End;{TList}

Procedure CopyFile(InFileName, var OutFileName: String);
Const
  BufSize = 4096; (* Huh? *)
Var
  InFile, OutFile: TStream;
  Buffer: Array[1..BufSize] Of Byte;
  ReadBufSize: Integer;
Begin
  InFile := Nil;
  OutFile := Nil;
  Try
    InFile := TFileStream.Create(InFileName, fmOpenRead);
    OutFile := TFileStream.Create(OutFileName, fmCreate);
    Repeat
      ReadBufSize := InFile.Read(Buffer, BufSize);
      OutFile.Write(Buffer, ReadBufSize);
    Until ReadBufSize<>BufSize;
    Log('File ''' + InFileName + ''' copied'#13#10);
  Finally
    InFile.Free;
    OutFile.Free;
  End;{Try}
End;{CopyFile}
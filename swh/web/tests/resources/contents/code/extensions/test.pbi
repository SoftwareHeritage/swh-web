﻿; PureBASIC 5 - Syntax Highlighting Example

Enumeration Test 3 Step 10
  #Constant_One ; Will be 3
  #Constant_Two ; Will be 13
EndEnumeration

A.i = #Constant_One
B = A + 3

STRING.s = SomeProcedure("Hello World", 2, #Empty$, #Null$)
ESCAPED_STRING$ = ~"An escaped (\\) string!\nNewline..."

FixedString.s{5} = "12345"

Macro XCase(Type, Text)
  Type#Case(Text)
EndMacro

StrangeProcedureCall ("This command is split " +
                      "over two lines") ; Line continuation example

If B > 3 : X$ = "Concatenation of commands" : Else : X$ = "Using colons" : EndIf

Declare.s Attach(String1$, String2$)

Procedure.s Attach(String1$, String2$)
  ProcedureReturn String1$+" "+String2$
EndProcedure

# lextab.py. This file automatically created by PLY (version 3.10). Don't edit!
_tabversion   = '3.10'
_lextokens    = set(('AUTO', 'BREAK', 'CASE', 'CHAR', 'CONST', 'CONTINUE', 'DEFAULT', 'DO', 'DOUBLE', 'ELSE', 'ENUM', 'EXTERN', 'FLOAT', 'FOR', 'GOTO', 'IF', 'INLINE', 'INT', 'LONG', 'REGISTER', 'OFFSETOF', 'RESTRICT', 'RETURN', 'SHORT', 'SIGNED', 'SIZEOF', 'STATIC', 'STRUCT', 'SWITCH', 'TYPEDEF', 'UNION', 'UNSIGNED', 'VOID', 'VOLATILE', 'WHILE', '__INT128', '_BOOL', '_COMPLEX', '_NORETURN', '_THREAD_LOCAL', '_STATIC_ASSERT', '_ATOMIC', '_ALIGNOF', '_ALIGNAS', 'ID', 'TYPEID', 'INT_CONST_DEC', 'INT_CONST_OCT', 'INT_CONST_HEX', 'INT_CONST_BIN', 'INT_CONST_CHAR', 'FLOAT_CONST', 'HEX_FLOAT_CONST', 'CHAR_CONST', 'WCHAR_CONST', 'U8CHAR_CONST', 'U16CHAR_CONST', 'U32CHAR_CONST', 'STRING_LITERAL', 'WSTRING_LITERAL', 'U8STRING_LITERAL', 'U16STRING_LITERAL', 'U32STRING_LITERAL', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'OR', 'AND', 'NOT', 'XOR', 'LSHIFT', 'RSHIFT', 'LOR', 'LAND', 'LNOT', 'LT', 'LE', 'GT', 'GE', 'EQ', 'NE', 'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL', 'LSHIFTEQUAL', 'RSHIFTEQUAL', 'ANDEQUAL', 'XOREQUAL', 'OREQUAL', 'PLUSPLUS', 'MINUSMINUS', 'ARROW', 'CONDOP', 'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'LBRACE', 'RBRACE', 'COMMA', 'PERIOD', 'SEMI', 'COLON', 'ELLIPSIS', 'PPHASH', 'PPPRAGMA', 'PPPRAGMASTR'))
_lexreflags   = 64
_lexliterals  = ''
_lexstateinfo = {'INITIAL': 'inclusive', 'ppline': 'exclusive', 'pppragma': 'exclusive'}
_lexstatere   = {'INITIAL': [('(?P<t_PPHASH>[ \\t]*\\#)|(?P<t_NEWLINE>\\n+)|(?P<t_LBRACE>\\{)|(?P<t_RBRACE>\\})|(?P<t_FLOAT_CONST>((((([0-9]*\\.[0-9]+)|([0-9]+\\.))([eE][-+]?[0-9]+)?)|([0-9]+([eE][-+]?[0-9]+)))[FfLl]?))|(?P<t_HEX_FLOAT_CONST>(0[xX]([0-9a-fA-F]+|((([0-9a-fA-F]+)?\\.[0-9a-fA-F]+)|([0-9a-fA-F]+\\.)))([pP][+-]?[0-9]+)[FfLl]?))|(?P<t_INT_CONST_HEX>0[xX][0-9a-fA-F]+(([uU]ll)|([uU]LL)|(ll[uU]?)|(LL[uU]?)|([uU][lL])|([lL][uU]?)|[uU])?)|(?P<t_INT_CONST_BIN>0[bB][01]+(([uU]ll)|([uU]LL)|(ll[uU]?)|(LL[uU]?)|([uU][lL])|([lL][uU]?)|[uU])?)', [None, ('t_PPHASH', 'PPHASH'), ('t_NEWLINE', 'NEWLINE'), ('t_LBRACE', 'LBRACE'), ('t_RBRACE', 'RBRACE'), ('t_FLOAT_CONST', 'FLOAT_CONST'), None, None, None, None, None, None, None, None, None, ('t_HEX_FLOAT_CONST', 'HEX_FLOAT_CONST'), None, None, None, None, None, None, None, ('t_INT_CONST_HEX', 'INT_CONST_HEX'), None, None, None, None, None, None, None, ('t_INT_CONST_BIN', 'INT_CONST_BIN')]), ('(?P<t_BAD_CONST_OCT>0[0-7]*[89])|(?P<t_INT_CONST_OCT>0[0-7]*(([uU]ll)|([uU]LL)|(ll[uU]?)|(LL[uU]?)|([uU][lL])|([lL][uU]?)|[uU])?)|(?P<t_INT_CONST_DEC>(0(([uU]ll)|([uU]LL)|(ll[uU]?)|(LL[uU]?)|([uU][lL])|([lL][uU]?)|[uU])?)|([1-9][0-9]*(([uU]ll)|([uU]LL)|(ll[uU]?)|(LL[uU]?)|([uU][lL])|([lL][uU]?)|[uU])?))|(?P<t_INT_CONST_CHAR>\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F])))){2,4}\')|(?P<t_CHAR_CONST>\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F]))))\')|(?P<t_WCHAR_CONST>L\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F]))))\')|(?P<t_U8CHAR_CONST>u8\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F]))))\')|(?P<t_U16CHAR_CONST>u\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F]))))\')|(?P<t_U32CHAR_CONST>U\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F]))))\')', [None, ('t_BAD_CONST_OCT', 'BAD_CONST_OCT'), ('t_INT_CONST_OCT', 'INT_CONST_OCT'), None, None, None, None, None, None, None, ('t_INT_CONST_DEC', 'INT_CONST_DEC'), None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, ('t_INT_CONST_CHAR', 'INT_CONST_CHAR'), None, None, None, None, None, None, ('t_CHAR_CONST', 'CHAR_CONST'), None, None, None, None, None, None, ('t_WCHAR_CONST', 'WCHAR_CONST'), None, None, None, None, None, None, ('t_U8CHAR_CONST', 'U8CHAR_CONST'), None, None, None, None, None, None, ('t_U16CHAR_CONST', 'U16CHAR_CONST'), None, None, None, None, None, None, ('t_U32CHAR_CONST', 'U32CHAR_CONST')]), ('(?P<t_UNMATCHED_QUOTE>(\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F]))))*\\n)|(\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F]))))*$))|(?P<t_BAD_CHAR_CONST>(\'([^\'\\\\\\n]|(\\\\(([a-wyzA-Z._~!=&\\^\\-\\\\?\'"]|x(?![0-9a-fA-F]))|(\\d+)(?!\\d)|(x[0-9a-fA-F]+)(?![0-9a-fA-F]))))[^\'\n]+\')|(\'\')|(\'([\\\\][^a-zA-Z._~^!=&\\^\\-\\\\?\'"x0-9])[^\'\\n]*\'))|(?P<t_WSTRING_LITERAL>L"([^"\\\\\\n]|(\\\\[0-9a-zA-Z._~!=&\\^\\-\\\\?\'"]))*")|(?P<t_U8STRING_LITERAL>u8"([^"\\\\\\n]|(\\\\[0-9a-zA-Z._~!=&\\^\\-\\\\?\'"]))*")|(?P<t_U16STRING_LITERAL>u"([^"\\\\\\n]|(\\\\[0-9a-zA-Z._~!=&\\^\\-\\\\?\'"]))*")|(?P<t_U32STRING_LITERAL>U"([^"\\\\\\n]|(\\\\[0-9a-zA-Z._~!=&\\^\\-\\\\?\'"]))*")|(?P<t_BAD_STRING_LITERAL>"([^"\\\\\\n]|(\\\\[0-9a-zA-Z._~!=&\\^\\-\\\\?\'"]))*([\\\\][^a-zA-Z._~^!=&\\^\\-\\\\?\'"x0-9])([^"\\\\\\n]|(\\\\[0-9a-zA-Z._~!=&\\^\\-\\\\?\'"]))*")|(?P<t_ID>[a-zA-Z_$][0-9a-zA-Z_$]*)|(?P<t_STRING_LITERAL>"([^"\\\\\\n]|(\\\\[0-9a-zA-Z._~!=&\\^\\-\\\\?\'"]))*")|(?P<t_ELLIPSIS>\\.\\.\\.)|(?P<t_LOR>\\|\\|)|(?P<t_PLUSPLUS>\\+\\+)|(?P<t_LSHIFTEQUAL><<=)|(?P<t_OREQUAL>\\|=)|(?P<t_PLUSEQUAL>\\+=)|(?P<t_RSHIFTEQUAL>>>=)|(?P<t_TIMESEQUAL>\\*=)|(?P<t_XOREQUAL>\\^=)', [None, ('t_UNMATCHED_QUOTE', 'UNMATCHED_QUOTE'), None, None, None, None, None, None, None, None, None, None, None, None, None, None, ('t_BAD_CHAR_CONST', 'BAD_CHAR_CONST'), None, None, None, None, None, None, None, None, None, None, ('t_WSTRING_LITERAL', 'WSTRING_LITERAL'), None, None, ('t_U8STRING_LITERAL', 'U8STRING_LITERAL'), None, None, ('t_U16STRING_LITERAL', 'U16STRING_LITERAL'), None, None, ('t_U32STRING_LITERAL', 'U32STRING_LITERAL'), None, None, ('t_BAD_STRING_LITERAL', 'BAD_STRING_LITERAL'), None, None, None, None, None, ('t_ID', 'ID'), (None, 'STRING_LITERAL'), None, None, (None, 'ELLIPSIS'), (None, 'LOR'), (None, 'PLUSPLUS'), (None, 'LSHIFTEQUAL'), (None, 'OREQUAL'), (None, 'PLUSEQUAL'), (None, 'RSHIFTEQUAL'), (None, 'TIMESEQUAL'), (None, 'XOREQUAL')]), ('(?P<t_ANDEQUAL>&=)|(?P<t_ARROW>->)|(?P<t_CONDOP>\\?)|(?P<t_DIVEQUAL>/=)|(?P<t_EQ>==)|(?P<t_GE>>=)|(?P<t_LAND>&&)|(?P<t_LBRACKET>\\[)|(?P<t_LE><=)|(?P<t_LPAREN>\\()|(?P<t_LSHIFT><<)|(?P<t_MINUSEQUAL>-=)|(?P<t_MINUSMINUS>--)|(?P<t_MODEQUAL>%=)|(?P<t_NE>!=)|(?P<t_OR>\\|)|(?P<t_PERIOD>\\.)|(?P<t_PLUS>\\+)|(?P<t_RBRACKET>\\])|(?P<t_RPAREN>\\))|(?P<t_RSHIFT>>>)|(?P<t_TIMES>\\*)|(?P<t_XOR>\\^)|(?P<t_AND>&)|(?P<t_COLON>:)|(?P<t_COMMA>,)|(?P<t_DIVIDE>/)|(?P<t_EQUALS>=)|(?P<t_GT>>)|(?P<t_LNOT>!)|(?P<t_LT><)|(?P<t_MINUS>-)|(?P<t_MOD>%)|(?P<t_NOT>~)|(?P<t_SEMI>;)', [None, (None, 'ANDEQUAL'), (None, 'ARROW'), (None, 'CONDOP'), (None, 'DIVEQUAL'), (None, 'EQ'), (None, 'GE'), (None, 'LAND'), (None, 'LBRACKET'), (None, 'LE'), (None, 'LPAREN'), (None, 'LSHIFT'), (None, 'MINUSEQUAL'), (None, 'MINUSMINUS'), (None, 'MODEQUAL'), (None, 'NE'), (None, 'OR'), (None, 'PERIOD'), (None, 'PLUS'), (None, 'RBRACKET'), (None, 'RPAREN'), (None, 'RSHIFT'), (None, 'TIMES'), (None, 'XOR'), (None, 'AND'), (None, 'COLON'), (None, 'COMMA'), (None, 'DIVIDE'), (None, 'EQUALS'), (None, 'GT'), (None, 'LNOT'), (None, 'LT'), (None, 'MINUS'), (None, 'MOD'), (None, 'NOT'), (None, 'SEMI')])], 'ppline': [('(?P<t_ppline_FILENAME>"([^"\\\\\\n]|(\\\\[0-9a-zA-Z._~!=&\\^\\-\\\\?\'"]))*")|(?P<t_ppline_LINE_NUMBER>(0(([uU]ll)|([uU]LL)|(ll[uU]?)|(LL[uU]?)|([uU][lL])|([lL][uU]?)|[uU])?)|([1-9][0-9]*(([uU]ll)|([uU]LL)|(ll[uU]?)|(LL[uU]?)|([uU][lL])|([lL][uU]?)|[uU])?))|(?P<t_ppline_NEWLINE>\\n)|(?P<t_ppline_PPLINE>line)', [None, ('t_ppline_FILENAME', 'FILENAME'), None, None, ('t_ppline_LINE_NUMBER', 'LINE_NUMBER'), None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, ('t_ppline_NEWLINE', 'NEWLINE'), ('t_ppline_PPLINE', 'PPLINE')])], 'pppragma': [('(?P<t_pppragma_NEWLINE>\\n)|(?P<t_pppragma_PPPRAGMA>pragma)|(?P<t_pppragma_STR>.+)', [None, ('t_pppragma_NEWLINE', 'NEWLINE'), ('t_pppragma_PPPRAGMA', 'PPPRAGMA'), ('t_pppragma_STR', 'STR')])]}
_lexstateignore = {'INITIAL': ' \t', 'ppline': ' \t', 'pppragma': ' \t'}
_lexstateerrorf = {'INITIAL': 't_error', 'ppline': 't_ppline_error', 'pppragma': 't_pppragma_error'}
_lexstateeoff = {}

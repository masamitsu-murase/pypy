
// We hand craft these in module/support.ll
char *RPyString_AsString(RPyString*);
int RPyString_Size(RPyString*);
RPyString *RPyString_FromString(char *);
int RPyExceptionOccurred(void);

void raisePyExc_IOError(char *);
void raisePyExc_ValueError(char *);
void raisePyExc_OverflowError(char *);
void raisePyExc_ZeroDivisionError(char *);
void raisePyExc_RuntimeError(char *);
void raisePyExc_thread_error(char *);

#define RPyRaiseSimpleException(exctype, errormsg) raise##exctype(errormsg)

// Generated by rpython - argggh have to feed in prototypes
RPyFREXP_RESULT *ll_frexp_result(double, int);
RPyMODF_RESULT *ll_modf_result(double, double);
RPySTAT_RESULT *ll_stat_result(int, int, int, int, int, int, int, int, int, int);
void RPYTHON_RAISE_OSERROR(int error);

RPyListOfString *_RPyListOfString_New(int);
void _RPyListOfString_SetItem(RPyListOfString *, int, RPyString *);

#include <errno.h>
#include <locale.h>
#include <ctype.h>

//the placeholder in the next line gets replaced by the actual python.h path
#include __PYTHON_H__

// overflows/zeros/values raising operations
__RAISING_OPS__

// Append some genc files here manually from python
__INCLUDE_FILES__

#ifdef ENTRY_POINT_DEFINED

#include <gc/gc.h>

char *RPython_StartupCode() {
  GC_all_interior_pointers = 0;
  return NULL;
}

int entry_point(RPyListOfString *);

int main(int argc, char *argv[])
{
    char *errmsg;
    int i, exitcode;
    RPyListOfString *list;
    errmsg = RPython_StartupCode();
    if (errmsg) goto error;
    
    list = _RPyListOfString_New(argc);
    if (RPyExceptionOccurred()) goto memory_out;
    for (i=0; i<argc; i++) {
      RPyString *s = RPyString_FromString(argv[i]);

      if (RPyExceptionOccurred()) {
	goto memory_out;
      }

      _RPyListOfString_SetItem(list, i, s);
    }

    exitcode = entry_point(list);

    if (RPyExceptionOccurred()) {
      goto error; // XXX see genc
    }
    return exitcode;

 memory_out:
    errmsg = "out of memory";
 error:
    fprintf(stderr, "Fatal error during initialization: %s\n", errmsg);
    return 1;
}

#endif /* ENTRY_POINT_DEFINED */


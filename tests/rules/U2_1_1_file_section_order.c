/* U2.1.1 violation: include appears after a function definition. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
int start(void)
{
    return 0;
}

/* ============================================================================ */
/*                              Include Files                                  */
/* ============================================================================ */
/* review-comment -- Include Files 'stddef.h' is after Function Definitions 'start', but Include Files should come first */
#include <stddef.h>

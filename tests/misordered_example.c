/* Deliberately invalid C layout example. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
void start(void)
{
}

/* ============================================================================ */
/*                              Include Files                                  */
/* ============================================================================ */
/* review comment: Include Files 'stddef.h' is after Function Definitions 'start', but Include Files should come first */
#include <stddef.h>


/* review comment: static prototype 'stop' is below 'Include Files', but should be below 'Static Function Prototypes' */
static void stop(void);

/* ============================================================================ */
/*                                 Typedefs                                    */
/* ============================================================================ */
/* review comment: Typedefs 'state_t' is after Static Function Prototypes 'stop', but Typedefs should come first */
typedef unsigned int state_t;

/* ============================================================================ */
/*                              Macros                                          */
/* ============================================================================ */
/* review comment: Macros 'STATE_READY' is after Typedefs 'state_t', but Macros should come first */
#define STATE_READY 1

/* ============================================================================ */
/*                      Static Function Definitions                            */
/* ============================================================================ */
static void stop(void)
{
}

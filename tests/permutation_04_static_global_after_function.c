/* Permutation 04: static global after function. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
void execute(void) {}

/* ============================================================================ */
/*                            Static Variables                                 */
/* ============================================================================ */
/* review comment: Static Variables 'state' is after Function Definitions 'execute', but Static Variables should come first */
static int state;

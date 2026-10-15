/* U10.5.2 violation: void function has no explicit final return. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
void finish(void)
{
    int status = 1;
    (void)status;
/* review-comment -- void function 'finish' must end with an explicit return statement */
}

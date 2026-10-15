/* U10.5.1 violation: function has more than one return statement. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
int choose(int value)
{
    if (value > 0) {
        return 1;
    }
/* review-comment -- function 'choose' has multiple return statements; use one return at the end */
    return 0;
}

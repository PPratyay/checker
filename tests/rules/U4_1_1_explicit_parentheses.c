/* U4.1.1 violation: complex expression lacks explicit parentheses. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
int calculate(int a, int b, int c)
{
/* review-comment -- complex expression has multiple operators without explicit parentheses for precedence */
    return a + b * c;
}

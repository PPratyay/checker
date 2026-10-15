/* U4.1.2 violation: increment is combined with another expression. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
void update(int *value)
{
/* review-comment -- increment/decrement must be an isolated statement; do not combine it with other operators or expressions */
    *value = (*value)++;
    return;
}

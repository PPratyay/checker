/* Valid examples for the additional rules. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
int calculate(int left, int right)
{
    return (left + right) * (left - right);
}

void update(int *value)
{
    (*value)++;
    return;
}

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
int choose(int value)
{
    int result = 0;
    if (value > 0) {
        result = 1;
    }
    return result;
}

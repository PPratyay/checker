/* Deliberately invalid examples for the additional rules. */

/* ============================================================================ */
/*                           Function Definitions                              */
/* ============================================================================ */
int calculate(int a, int b, int c)
{
    return a + b * c;
}

void update(int *value)
{
    result = (*value)++;
}

int choose(int value)
{
    if (value > 0) {
        return 1;
    }
    return 0;
}

void finish(void)
{
    value = 1;
}

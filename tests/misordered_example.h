/* Deliberately invalid header layout example. */

/* ============================================================================ */
/*                              Include Files                                  */
/* ============================================================================ */
#include <stddef.h>

/* ============================================================================ */
/*                                 Typedefs                                    */
/* ============================================================================ */
typedef unsigned int item_count_t;

/* review comment: include guard appears after the first code section */
#ifndef MISORDERED_EXAMPLE_H
#define MISORDERED_EXAMPLE_H

/* ============================================================================ */
/*                                  Macros                                     */
/* ============================================================================ */
/* review comment: Macros 'MISORDERED_EXAMPLE_VERSION' is after Typedefs 'item_count_t', but Macros should come first */
#define MISORDERED_EXAMPLE_VERSION 1

#endif

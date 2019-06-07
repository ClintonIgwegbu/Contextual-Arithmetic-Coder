from math import floor, ceil
from bisect import bisect
from vl_codes import *


def init_context_history():
    """ Create contextual history data structure allowing a maximum order of 3. """
    ord0 = {}
    ord1 = {}
    ord2 = {}
    ord3 = {}
    seen_contexts = [ord0, ord1, ord2, ord3]

    return seen_contexts


def drop_to_sub_context(context):
    order = len(context)
    if order == 0:
        pass
    elif order == 1:
        context = ""
    else:  # order >= 2
        context = context[1:]

    return context


def get_prob(seen_contexts, max_context):  # max_order=3):
    """ Update probability distribution. """
    P = [0.0] * 256
    F = [0.0] * 257
    k = 0

    alphabet = [chr(i) for i in range(256)]

    for symbol in alphabet:
        p = 1  # initialise prob. of next symbol to 1
        context = max_context
        order = len(context)
        excluded = []  # list of excluded characters

        # iterate through orders decreasingly to GET PROBABILITY
        while order >= -1:

            exclude_count = 0  # total count of excluded characters appearances within context

            if order == -1:
                C = 256 - len(excluded)
                p *= 1/C
                break

            if context in seen_contexts[order]:  # if context seen already
                for character in excluded:
                    exclude_count += seen_contexts[order][context].get(character, 0)

                C = seen_contexts[order][context]['total'] - exclude_count # get post-exclusion context count
                assert C >= 0, 'C is negative'

                if not(symbol in seen_contexts[order][context]):  # character is new to context
                    e = 1 / (C + 1)  # calculate escape sequence code space
                    p *= e  # update probability
                    assert p != 0, "0 probability"

                    for character in seen_contexts[order][context]:  # update list of excluded characters
                        if not(character in excluded) and (character != 'total'):
                            excluded.append(character)  # append character to list of excluded letters

                    context = drop_to_sub_context(context)

                else:  # if CHARACTER SEEN ALREADY
                    c = seen_contexts[order][context][symbol]  # get contextual character count
                    e = 1 / (C + 1)  # calculate escape sequence code space
                    code_space = c / C * (1 - e)  # calculate code space for character in given order
                    p *= code_space  # update probability
                    assert p != 0, "0 probability"
                    break  # stop decreasing order

            else:  # CONTEXT NOT SEEN YET
                context = drop_to_sub_context(context)

            order -= 1

        P[k] = p
        F[k + 1] = F[k] + p
        k += 1

    F.pop()
    return P, F


def update_history(x, seen_contexts, max_context, freq_count, max_order=2):
    """ Update context considered and contextual history. """
    context = max_context
    order = len(context)

    while order >= -1:  # iterate downwards through orders
        if order == -1:
            seen_contexts[0][""][x] = 1  # character has now been seen so include it in order 0
            freq_count += 1
            break

        if context in seen_contexts[order]:  # CONTEXT PREVIOUSLY SEEN
            if not(x in seen_contexts[order][context]):  # NEW CHARACTER SEEN (within context)
                seen_contexts[order][context][x] = 1  # add letter to context dictionary
                seen_contexts[order][context]['total'] += 1  # increment context count
                freq_count += 1

                context = drop_to_sub_context(context)

            else:  # CHARACTER ALREADY SEEN (within context)
                seen_contexts[order][context][x] += 1  # increment character's contextual freq. count
                seen_contexts[order][context]['total'] += 1  # increment context count
                freq_count += 1
                break  # stop decreasing order

        else:  # CONTEXT NOT SEEN YET
            # add context to dictionary and increment character count for context
            seen_contexts[order][context] = {}  # add item to order dict. with key context and value empty dict.
            seen_contexts[order][context]['total'] = 1  # add key 'total' to empty dict. with value of 1
            seen_contexts[order][context][x] = 1  # add key x to dict. with value of 1
            freq_count += 1

            context = drop_to_sub_context(context)
        order -= 1

    # UPDATE max_context string
    if len(max_context) < max_order:
        max_context = max_context + x  # concatenate x to the end of context string

    else:
        if max_order == 0:
            pass
        else:  # max_order >= 1:
            max_context = drop_to_sub_context(max_context) + x

    # print(freq_count)
    return max_context, freq_count


def encode(x):
    precision = 32
    one = int(2**precision - 1)
    quarter = int(ceil(one / 4))
    half = 2 * quarter
    threequarters = 3 * quarter

    y = []  # initialise output list
    lo, hi = 0, one  # initialise lo and hi to be [0,1.0)
    straddle = 0  # straddle counter
    
    seen_contexts = init_context_history()
    max_context = ""
    freq_count = 0

    for k in range(len(x)):  # for every symbol
        # progress bar
        if k % 10000 == 0:
            print('Arithmetic encoded %d%%    \r' % int(floor(k / len(x) * 100)))

        lohi_range = hi - lo + 1  # added 1 avoids rounding issues

        ascii = ord(x[k])

        # GET PROB.
        P, F = get_prob(seen_contexts, max_context)
        lo = lo + int(ceil(lohi_range * F[ascii]))
        hi = lo + int(floor(lohi_range * P[ascii]))

        if lo == hi:
            raise NameError('Zero interval!')

        # UPDATE model history
        max_context, freq_count = update_history(x[k], seen_contexts, max_context, freq_count)

        # Re-scale the interval and output
        while True:
            if hi < half:
                y.append(0)
                y.extend(straddle * [1])
                straddle = 0 

            elif lo >= half:
                y.append(1)  # append a 1 to the output list y
                y.extend(straddle * [0])  # extend 'straddle' zeros
                straddle = 0  # reset the straddle counter
                lo = lo - half
                hi = hi - half  # subtract half from lo and hi

            elif lo >= quarter and hi < threequarters:
                straddle += 1
                lo = lo - quarter
                hi = hi - quarter

            else:
                break  # we break the infinite loop if the interval has reached an un-stretchable state

            # stretch
            lo = lo * 2
            hi = hi * 2 + 1
        
    # after processing all input symbols, flush any bits still in the 'straddle' pipeline
    straddle += 1  # adding 1 to straddle for "good measure" (ensures prefix-freeness)
    if lo < quarter:  # the position of lo determines the dyadic interval that fits
        y.append(0)  # output a zero followed by "straddle" ones
        y.extend(straddle * [1])
    else:
        y.append(1)  # output a 1 followed by "straddle" zeros
        y.extend(straddle * [0])

    return y


def decode(y):
    precision = 32
    one = int(2 ** precision - 1)
    quarter = int(ceil(one / 4))
    half = 2 * quarter
    threequarters = 3 * quarter

    y.extend(precision * [0])  # dummy zeros to prevent index out of bound errors
    # initialise by taking first 'precision' bits from y and converting to a number
    value = int(''.join(str(a) for a in y[0:precision]), 2)
    position = precision  # position where currently reading y
    lo, hi = 0, one

    x = []

    seen_contexts = init_context_history()
    max_context = ""
    freq_count = 0

    alphabet = [chr(i) for i in range(256)]

    while position < len(y):
        if position % 1000 == 0:
            print('Arithmetic decoded %d%%    \r' % int(floor(position / len(y) * 100)))

        lohi_range = hi - lo + 1

        # GET PROB. -> we must do this so that we can find where value lies within the distribution -> then when
        # we are done we change the interval end-points, then find where new value lies within new interval
        # then by the next iteration we have updated the prob. distribution
        # we are using the prob. the dist. that was used to encode the letter we just decoded
        P, F = get_prob(seen_contexts, max_context)

        a = bisect(F, (value - lo) / lohi_range) - 1
        x.append(alphabet[a])  # output alphabet[a]

        lo = lo + int(ceil(lohi_range * F[a]))
        hi = lo + int(floor(lohi_range * P[a]))

        if (lo == hi):
            raise NameError('Zero interval!')

        # UPDATE HISTORY
        max_context, freq_count = update_history(x[-1], seen_contexts, max_context, freq_count)

        while position < len(y):
            if hi < half:
                # do nothing
                pass
            elif lo >= half:
                lo = lo - half
                hi = hi - half
                value = value - half
            elif lo >= quarter and hi < threequarters:
                lo = lo - quarter
                hi = hi - quarter
                value = value - quarter
            else:
                break
            lo = 2 * lo
            hi = 2 * hi + 1
            value = 2 * value + y[position]
            position += 1

    return x




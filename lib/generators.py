from random import randint

# -------------ALGOS GENERATORS----------------

def ascending(limit, chars, min):
    next = False
    nbs = [chars.index(c) for c in min][::-1]
    converted = [chars.index(c) for c in limit][::-1]
    for length in range(len(min), len(limit)+1):
        if next:
            nbs = [0]*(length-1)+[1]
        next = False
        end = False
        while 1:
            link = "".join([chars[c] for c in nbs][::-1])
            yield link
            while nbs[0] != len(chars)-1:
                nbs[0] += 1
                link = "".join([chars[c] for c in nbs][::-1])
                yield link
                if nbs == converted:
                    end = True
                    break
                elif nbs == [len(chars)-1]*length:
                    next = True
                    break
            if next or end:
                break
            if nbs[0] == len(chars)-1:
                count = 0
                for nb in nbs:
                    if nb == len(chars)-1:
                        nbs[count] = 0
                        count += 1
                    else:
                        nbs[count] += 1
                        break
        if end:
            break
            

def descending(limit, chars, min):
    next = False
    min_nbs = [chars.index(c) for c in min][::-1]
    nbs = [chars.index(c) for c in limit][::-1]
    for length in list(range(len(min), len(limit)+1))[::-1]:
        if next:
            nbs = [len(chars)-1]*(length)
        next = False
        end = False
        while 1:
            link = "".join([chars[c] for c in nbs][::-1])
            yield link
            while nbs[0] != 0:
                nbs[0] -= 1
                link = "".join([chars[c] for c in nbs][::-1])
                yield link
                if nbs == min_nbs:
                    end = True
                    break
                elif nbs == [0]*(length-1)+[1]:
                    next = True
                    break
            if next or end:
                break
            if nbs[0] == 0:
                count = 0
                for nb in nbs:
                    if nb == 0:
                        nbs[count] = len(chars)-1
                        count += 1
                    else:
                        nbs[count] -= 1
                        break
        if end:
            break

def random(limit, chars, min):
    while 1: # To generate indefinitely
        converted = [chars.index(c) for c in limit]
        link = ""
        length = randint(len(min), len(limit))
        if length >= len(limit):
            edge = True
        else:
            edge = False
        for i in range(0, len(limit)):
            while 1:
                n = randint(0, len(chars)-1)
                if i == 0 and chars[n] == "0":
                    continue
                if edge:
                    if n > converted[i] :
                        continue
                    elif n < converted[i]:
                        edge = False
                        break
                    else:
                        break
                else:
                    break

            link += chars[n]
            if i == length-1:
                break

        yield link

# ---------------------------------------------
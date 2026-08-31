def return_int_if_numbers(string):
    if string.lstrip("-").isdecimal():
        return int(string)
    return string

def round_to_nearest_five(number):
    return 5 * round(number / 5)
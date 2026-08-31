def return_int_if_numbers(string):
    if string.lstrip("-").isdecimal():
        return int(string)
    return string

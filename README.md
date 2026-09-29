def anagram(str1, str2):
    str1 = sorted(str1)
    str2 = sorted(str2)

    result = str1 == str2

    return result


print(anagram("raza", "zara"))
print(anagram("hello", "world")) 


jo bhi ye delete karenga vo bhadwa hai

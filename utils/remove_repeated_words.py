def remove_repeated_words(text):
    words = text.split()
    filtered_words = [words[0]]

    for word in words[1:]:
        if (
            word != filtered_words[-1]
        ):  # If the current word is not the same as the previous word
            filtered_words.append(word)

    filtered_text = " ".join(filtered_words)
    return filtered_text

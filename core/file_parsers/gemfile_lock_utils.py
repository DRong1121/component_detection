import re
import string

import unicodedata
import chardet


MIN_LEN = 4
MIN_LEN_STR = b'4'

punctuation = re.escape(b"""!"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~""")
whitespaces = b' \\t\\n\\r\t\n\r'
printable = b'A-Za-z0-9' + whitespaces + punctuation
null_byte = b'\x00'

_ascii_pattern = (
    # plain ASCII is a sequence of printable of a minimum length
      b'('
    + b'[' + printable + b']'
    + b'{' + MIN_LEN_STR + b',}'
    + b')'
    # or utf-16-le-encoded ASCII is a sequence of ASCII+null byte
    + b'|'
    + b'('
    + b'(?:' + b'[' + printable + b']' + null_byte + b')'
    + b'{' + MIN_LEN_STR + b',}'
    + b')'
)

ascii_strings = re.compile(_ascii_pattern).finditer

replace_literal_line_returns = re.compile('[\\n\\r]+$').sub


def normalize_line_ends(s):
    """
    Replace trailing literal line returns by real line return (e.g. POSIX LF aka. \n) in string `s`.
    """
    return replace_literal_line_returns('\n', s)


remove_junk = re.compile('[' + punctuation.decode('utf-8') + whitespaces.decode('utf-8') + ']').sub
JUNK = frozenset(string.punctuation + string.digits + string.whitespace)


def clean_string(s, min_len=MIN_LEN, junk=JUNK):
    """
    Yield cleaned strings from string s if it passes some validity tests:
     * not made of white spaces
     * with a minimum length ignoring spaces and punctuations
     * not made of only two repeated character
     * not made of only of digits, punctuations and whitespaces
    """
    s = s.strip()

    def valid(st):
        st = remove_junk('', st)
        return (st and len(st) >= min_len
                # ignore character repeats, e.g need more than two unique characters
                and len(set(st.lower())) > 1
                # ignore string made only of digits, spaces or punctuations
                and not all(c in junk for c in st))

    if valid(s):
        yield s.strip()


def decode(s):
    """
    Return a decoded unicode string from s or None if the string cannot be decoded.
    """
    if b'\x00' in s:
        try:
            return s.decode('utf-16-le')
        except UnicodeDecodeError:
            pass
    else:
        return s.decode('ascii')


def strings_from_string(binary_string, clean=False, min_len=0):
    """
    Yield strings extracted from a (possibly binary) string `binary_string`. The
    strings are ASCII printable characters only. If `clean` is True, also clean
    and filter short and repeated strings. Note: we do not keep the offset of
    where a string was found (e.g. match.start).
    """
    for match in ascii_strings(binary_string):
        s = decode(match.group())
        if not s:
            continue
        s = normalize_line_ends(s)
        for line in s.splitlines(False):
            line = line.strip()
            if len(line) < min_len:
                continue

            if clean:
                for ss in clean_string(line, min_len=min_len):
                    yield ss
            else:
                yield line


def string_from_string(binary_string, clean=False, min_len=0):
    """
    Return a unicode string string extracted from a (possibly binary) string,
    removing all non printable characters.
    """
    return u' '.join(strings_from_string(binary_string, clean, min_len))


def remove_null_bytes(s):
    """
    Return a string replacing by a space all null bytes.
    There are some rare cases where we can have binary strings that are not
    caught early when detecting a file type, but only late at the line level.
    This help catch most of these cases.
    """
    return s.replace('\x00', ' ')


def as_unicode(line):
    """
    Return a unicode text line from a text line.
    Try to decode line as Unicode. Try first some default encodings,
    then attempt Unicode trans-literation and finally
    fall-back to ASCII strings extraction.
    TODO: Add file/magic detection, unicodedmanit/BS3/4
    """
    if isinstance(line, str):
        return remove_null_bytes(line)

    try:
        s = line.decode('UTF-8')
    except UnicodeDecodeError:
        try:
            # FIXME: latin-1 may never fail
            s = line.decode('LATIN-1')
        except UnicodeDecodeError:
            try:
                # Convert some byte string to ASCII characters as Unicode including
                # replacing accented characters with their non- accented NFKD
                # equivalent. Non ISO-Latin and non ASCII characters are stripped
                # from the output. Does not preserve the original length offsets.
                # For Unicode NFKD equivalence, see:
                # http://en.wikipedia.org/wiki/Unicode_equivalence
                s = unicodedata.normalize('NFKD', line).encode('ASCII')
            except UnicodeDecodeError:
                try:
                    enc = chardet.detect(line)['encoding']
                    s = str(line, enc)
                except UnicodeDecodeError:
                    # fall-back to strings extraction if all else fails
                    s = string_from_string(s)
    return remove_null_bytes(s)


def remove_verbatim_cr_lf_tab_chars(s):
    """
    Return a string replacing by a space any verbatim but escaped line endings
    and tabs (such as a literal \n or \r \t).
    """
    if not s:
        return s
    return s.replace('\\r', ' ').replace('\\n', ' ').replace('\\t', ' ')


def unicode_text_lines(location):
    """
    Return an iterable over unicode text lines from a file at `location` if it
    contains text. Open the file as binary with universal new lines then try to
    decode each line as Unicode.
    """
    with open(location, 'rb') as f:
        for line in f.read().splitlines(True):
            yield remove_verbatim_cr_lf_tab_chars(as_unicode(line))

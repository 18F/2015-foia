import re


def agency_description(doc):
    """Account for BRs and such while finding the description."""
    description = ""
    # All text after the last h2, excluding that h2's text
    for el in list(doc("h2")[-1].next_elements)[1:]:
        if not el.name:
            description += el.string.strip()
        # Only want one new line when there are two BRs
        elif el.name == "br" and not description.endswith("\n"):
            description += "\n"
    return description.strip()


def clean_paragraphs(doc):
    """Find all paragraphs with content. Return paragraph els + content
    strings. Beautiful Soup doesn't handle unclosed tags very graciously, so
    account for paragraphs within paragraphs."""
    lines, ps = [], []
    for p in doc("p"):
        for child in p.contents:
            # child is a text element or a link
            if child.name in (None, 'a') and child.string.strip():
                lines.append(child.string.strip())
                ps.append(p)
    return lines, ps


PHONE_RE = re.compile(
    r"""(?P<prefix>\+?[\d\s\(\)\-]*)"""
    r"""(?P<area_code>\(?\d{3}\)?[\s\-\(\)]*)"""
    r"""(?P<first_three>\d{3}[\-\s\(\)]*)"""
    r"""(?P<last_four>\d{4})""", re.IGNORECASE)


def phone(line):
    """Given "(123) 456-7890 (Telephone)", extract the number"""
    match = PHONE_RE.search(line)
    if match:
        # kill all non-numbers
        prefix = "".join(ch for ch in match.group("prefix") if ch.isdigit())
        area_code = "".join(ch for ch in match.group("area_code")
                            if ch.isdigit())
        first_three = "".join(ch for ch in match.group("first_three")
                              if ch.isdigit())
        last_four = "".join(ch for ch in match.group("last_four")
                            if ch.isdigit())
        number = "-".join([area_code, first_three, last_four])
        if prefix:
            return "+" + prefix + " " + number
        else:
            return number
    else:
        raise Exception("Error extracting phone number",
                        "phone line: " + line)


def split_address_from(lines):
    """Address goes until we find a phone or service center. Separate lines
    into address lines and remaining"""
    address, remaining = [], []
    cues = ("phone", "fax", "service center")
    for line in lines:
        if remaining:   # already switched over
            remaining.append(line)
        elif PHONE_RE.search(line) and any(q in line.lower() for q in cues):
            remaining.append(line)
        else:
            # Separate line breaks
            address.extend(re.split(r"[\n\r]+", line))
    if not remaining:
        raise Exception("error finding address end", lines)
    else:
        return address, remaining


def find_emails(lines, ps):
    """Find email address, then associated mailto"""
    email_re = re.compile(r"\be\-?mail", re.IGNORECASE)
    emails = []
    for idx, line in enumerate(lines):
        if email_re.search(line):
            a = ps[idx].a
            if a:
                emails_str = a["href"].replace("mailto:", "").strip()
                if "http://" not in emails_str:
                    emails.extend(re.split(r";\s*", emails_str))
            else:
                raise Exception("Error extracting email", line, idx,
                                ps[idx].prettify())
    return emails


def find_bold_fields(ps):
    """Remaining fields: website, request form, anything else"""
    simple_search = ["service center", "public liaison", "notes",
                     "foia officer"]
    link_search = ["website", "request form"]
    for p in ps:
        strong = p.strong
        text = strong.string.replace(":", "").strip() if strong else ""
        lower = text.lower()
        if strong and text != "FOIA Contact":
            value = strong.next_sibling.string.strip()
            yielded = False
            for term in simple_search:
                if term in lower:
                    yield term.replace(" ", "_"), value
                    yielded = True

            for term in link_search:
                if term in lower:
                    if p.a:
                        yield term.replace(" ", "_"), p.a["href"].strip()
                        yielded = True
                    else:
                        raise Exception("error extracting " + term,
                                        p.prettify())
            if not yielded:
                # FTC: FOIA Hotline
                # GSA: Program Manager
                yield "misc", (text, value)


def parse_department(elem, name):
    """Get data from a 'div' (elem) associated with a single department"""
    data = {"name": name}
    lines, ps = clean_paragraphs(elem)
    # remove first el (which introduces the section)
    lines, ps = lines[1:], ps[1:]

    address, lines = split_address_from(lines)
    data['address'] = address
    ps = ps[-len(lines):]   # Also throw away associated paragraphs
    for line in lines:
        lower = line.lower()
        if ('phone' in lower and 'public liaison' not in lower
                and 'service center' not in lower and 'phone' not in data):
            data['phone'] = phone(line)
        elif 'fax' in lower and 'fax' not in data:
            data['fax'] = phone(line)
    emails = find_emails(lines, ps)
    if emails:
        data['emails'] = emails
    for key, value in find_bold_fields(ps):
        if key == 'misc':
            misc_key, misc_value = value
            if 'misc' not in data:
                data['misc'] = {}
            data['misc'][misc_key] = misc_value
        else:
            data[key] = value
    return data
"""
  # first, get address - starts with line 2, then goes until we find a
    if fax == "(256) 544-007 (Fax)"
      fax = "(256) 544-0007" # fix, see http://foia.msfc.nasa.gov/reading.html
    end
"""

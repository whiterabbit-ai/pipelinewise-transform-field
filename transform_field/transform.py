import hashlib
import re

from dateutil import parser


def is_transform_required(record, when):
    """Detects if the transformation is required or not based on
    the defined conditions and the actual values in a record"""
    transform_required = False

    # Check if conditional transformation matches criteria
    if when:

        # Evaluate every condition
        for condition in when:
            column_to_match = condition.get('column')
            column_value = record.get(column_to_match, "")
            cond_equals = condition.get('equals')
            cond_pattern = condition.get('regex_match')

            # Exact condition
            if cond_equals:
                if column_value == cond_equals:
                    transform_required = True
                else:
                    transform_required = False
                    break

            # Regex based condition
            if cond_pattern:
                matcher = re.compile(cond_pattern)
                if matcher.search(column_value):
                    transform_required = True

                # Condition does not meet, exit the loop
                else:
                    transform_required = False
                    break

    # Transformation is always required if 'when' condition not defined
    else:
        transform_required = True

    return transform_required


def do_transform(record, field, trans_type, when=None):
    """Transform a value by a certain transformation type.
    Optionally can set conditional criteria based on other
    values of the record"""
    try:
        value = record.get(field)

        # Do transformation only if required
        if is_transform_required(record, when):

            # Transforms any input to NULL
            if trans_type == "SET-NULL":
                return_value = None

            # Transforms string input to hash
            elif trans_type == "HASH":
                return_value = hashlib.sha256(value.encode('utf-8')).hexdigest()

            # Transforms string input to hash skipping first n characters, e.g. HASH-SKIP-FIRST-2
            elif 'HASH-SKIP-FIRST' in trans_type:
                return_value = value[:int(trans_type[-1])] + \
                               hashlib.sha256(value.encode('utf-8')[int(trans_type[-1]):]).hexdigest()

            # Transforms any date to stg
            elif trans_type == "MASK-DATE":
                return_value = parser.parse(value).replace(month=1, day=1).isoformat()

            # Transforms any number to zero
            elif trans_type == "MASK-NUMBER":
                return_value = 0

            # Transforms any value to "hidden"
            elif trans_type == "MASK-HIDDEN":
                return_value = 'hidden'

            # Transforms string input to masked version skipping first and last n characters
            # e.g. MASK-STRING-SKIP-ENDS-3
            elif 'MASK-STRING-SKIP-ENDS' in trans_type:
                skip_ends_n = int(trans_type[-1])
                value_len = len(value)
                return_value = '*'*value_len if value_len <= (2 * skip_ends_n) \
                    else f'{value[:skip_ends_n]}{"*"*(value_len-(2*skip_ends_n))}{value[-skip_ends_n:]}'

            # Return the original value if cannot find transformation type
            # todo: is this the right behavior?
            else:
                return_value = value

        # Return the original value if cannot find transformation type
        else:
            return_value = value

        return return_value

    # Return the original value if cannot transform
    except Exception:
        return value

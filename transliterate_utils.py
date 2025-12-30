# Basic Phonetic Mapping for Tamil to English
# This is a best-effort mapper.

TAMIL_MAP = {
    # Vowels
    'அ': 'a', 'ஆ': 'aa', 'இ': 'i', 'ஈ': 'ee', 'உ': 'u', 'ஊ': 'oo', 
    'எ': 'e', 'ஏ': 'ea', 'ஐ': 'ai', 'ஒ': 'o', 'ஓ': 'oa', 'ஔ': 'au', 
    'ஃ': 'k',

    # Consonants
    'க்': 'k', 'ங்': 'ng', 'ச்': 'ch', 'ஞ்': 'gn', 'ட்': 't', 'ண்': 'n',
    'த்': 'th', 'ந்': 'n', 'ப்': 'p', 'ம்': 'm', 'ய்': 'y', 'ர்': 'r',
    'ல்': 'l', 'வ்': 'v', 'ழ்': 'zh', 'ள்': 'l', 'ற்': 'r', 'ன்': 'n',
    
    # Uyir-Mei (Vowel-Consonants) - Basic series (Example 'Ka')
    'க': 'ka', 'கா': 'kaa', 'கி': 'ki', 'கீ': 'kee', 'கு': 'ku', 'கூ': 'koo', 'கெ': 'ke', 'கே': 'kea', 'கை': 'kai', 'கொ': 'ko', 'கோ': 'koa', 'கௌ': 'kau',
    
    # Common mappings (simplified for implementation - a full map would be huge)
    # Ideally we handle unicode decomposition, but a simple replace list helps for common letters.
}

# A more robust approach uses unicode normalization, but for a simple script, 
# we can try to map based on standard unicode blocks if we iterate chars.
# However, python's replacements are easier for this constrained env.

def get_mapping():
    # Constructing a more usable map based on unicode properties would be better, 
    # but let's assume we can map the most common ones.
    # To save space, I will focus on the logic: 
    # Iterate characters, check if Tamil.
    pass

def transliterate_text(text):
    """
    Transliterates Tamil text to Tanglish (Phonetic English).
    This is an approximation.
    """
    if not isinstance(text, str):
        return ""
    
    # Vowels
    data = text
    
    # Map for Vowels
    data = data.replace('அ', 'a').replace('ஆ', 'aa').replace('இ', 'i').replace('ஈ', 'ee').replace('உ', 'u').replace('ஊ', 'oo')
    data = data.replace('எ', 'e').replace('ஏ', 'ea').replace('ஐ', 'ai').replace('ஒ', 'o').replace('ஓ', 'oa').replace('ஔ', 'au')
    
    # Map for Consonants + Vowel Signs (Simple Heuristic for common combinations)
    # Consonants with pulli (dot) -> pure consonant
    # Consonants without -> consonant + 'a'
    
    # We will use a library-free approach by iterating hex ranges if needed, 
    # but hardcoded replace is safer for strict "no internet" run.
    
    # Consonants
    replacements = [
        ('க்', 'k'), ('ங்', 'ng'), ('ச்', 'ch'), ('ஞ்', 'gn'), ('ட்', 't'), ('ண்', 'n'),
        ('த்', 'th'), ('ந்', 'n'), ('ப்', 'p'), ('ம்', 'm'), ('ய்', 'y'), ('ர்', 'r'),
        ('ல்', 'l'), ('வ்', 'v'), ('ழ்', 'zh'), ('ள்', 'l'), ('ற்', 'r'), ('ன்', 'n'),
        ('ஜ', 'j'), ('ஷ', 'sh'), ('ஸ', 's'), ('ஹ', 'h'), ('க்ஷ', 'ksh')
    ]
    for t, e in replacements:
        data = data.replace(t, e)

    # Base Consonants (Assuming implicit 'a')
    # Use a dictionary for fast lookup of base chars
    base_map = {
        'க': 'ka', 'ங': 'nga', 'ச': 'cha', 'ஞ': 'gna', 'ட': 'ta', 'ண': 'na',
        'த': 'tha', 'ந': 'na', 'ப': 'pa', 'ம': 'ma', 'ய': 'ya', 'ர': 'ra',
        'ல': 'la', 'வ': 'va', 'ழ': 'zha', 'ள': 'la', 'ற': 'ra', 'ன': 'na',
        'ஜ': 'ja', 'ஷ': 'sha', 'ஸ': 'sa', 'ஹ': 'ha'
    }
    
    # Vowel Signs (modifiers)
    # These effectively replace the implicit 'a' with another vowel. 
    # We need to process from Left to Right, but Tamil rendering is complex. 
    # In Unicode, consonant comes first, then modifier.
    # Ex: கி = க + இ (modifier)
    # We can handle this by replacing (Base + Modifier) sequences first.
    
    modifiers = [
         ('ா', 'aa'), ('ி', 'i'), ('ீ', 'ee'), ('ு', 'u'), ('ூ', 'oo'),
         ('ெ', 'e'), ('ே', 'ea'), ('ை', 'ai'), ('ொ', 'o'), ('ோ', 'oa'), ('ௌ', 'au')
    ]
    
    # We need to process strict combinations to correctly remove the 'a' from base.
    
    result = []
    i = 0
    chars = list(data)
    while i < len(chars):
        char = chars[i]
        
        # Check if it's a base consonant
        if char in base_map:
            # Check next char for modifier
            if i + 1 < len(chars) and chars[i+1] in [m[0] for m in modifiers]:
                # It's a combo
                mod_char = chars[i+1]
                mod_sound = next(m[1] for m in modifiers if m[0] == mod_char)
                base_sound = base_map[char][:-1] # Strip 'a'
                result.append(base_sound + mod_sound)
                i += 2
                continue
            # Check next char for Pulli (dot) which we handled in `replacements` 
            # actually `replacements` handled the pre-composed unicode chars if they exist, 
            # but usually they are separate. Let's explicitly check for pulli \u0bcd
            elif i + 1 < len(chars) and chars[i+1] == '்':
                 # Pure consonant
                 base_sound = base_map[char][:-1]
                 result.append(base_sound)
                 i += 2
                 continue
            else:
                # Standalone consonant -> 'a' sound
                result.append(base_map[char])
                i += 1
                continue
        else:
            # Just append as is (vowels or english or other)
            result.append(char)
            i += 1
            
    return "".join(result)

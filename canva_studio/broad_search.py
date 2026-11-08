"""Short topic searches; actions are preferences rather than requirements."""
import re,unicodedata
from .core import norm

TOPICS=[
 # Named foods must not become generic health/organ footage from benefit clauses.
 ('hạt điều',['hạt điều','cashew nuts','cashews'],['cashew','hạt điều']),
 ('óc chó',['hạt óc chó','walnuts','walnut kernels'],['walnut','óc chó']),
 ('củ lạc|đậu phộng|hạt lạc|lạc rang',['đậu phộng','củ lạc','peanuts'],['peanut','groundnut','đậu phộng','củ lạc','hạt lạc']),
 ('hạnh nhân',['hạnh nhân','almonds'],['almond','hạnh nhân']),
 ('hạt chia',['hạt chia','chia seeds'],['chia','hạt chia']),
 ('hạt lanh',['hạt lanh','flax seeds'],['flax','linseed','hạt lanh']),
 ('hạt bí',['hạt bí','pumpkin seeds'],['pumpkin seed','pepita','hạt bí']),
 ('hạt hướng dương',['hạt hướng dương','sunflower seeds'],['sunflower seed','hạt hướng dương']),
 ('bông cải xanh|súp lơ xanh',['bông cải xanh','broccoli'],['broccoli','bông cải xanh','súp lơ xanh']),
 ('cải bó xôi|rau bina',['cải bó xôi','spinach'],['spinach','rau bina','cải bó xôi']),
 ('cải xoăn',['cải xoăn','kale'],['kale','cải xoăn']),
 ('cà rốt',['cà rốt','carrots'],['carrot','cà rốt']),
 ('cà chua',['cà chua','tomatoes'],['tomato','cà chua']),
 ('khoai lang',['khoai lang','sweet potato'],['sweet potato','khoai lang']),
 ('củ dền',['củ dền','beetroot'],['beetroot','beet','củ dền']),
 ('dưa chuột|dưa leo',['dưa chuột','cucumber'],['cucumber','dưa chuột','dưa leo']),
 ('bí đỏ|bí ngô',['bí đỏ','pumpkin'],['pumpkin','bí đỏ','bí ngô']),
 ('quả bơ|trái bơ',['quả bơ','avocado'],['avocado','quả bơ']),
 ('chuối',['chuối','bananas'],['banana','chuối']),
 ('quả táo|trái táo|táo đỏ',['quả táo','apples'],['apple','quả táo']),
 ('việt quất',['việt quất','blueberries'],['blueberry','blueberries','việt quất']),
 ('đu đủ',['đu đủ','papaya'],['papaya','đu đủ']),
 ('chanh',['chanh','lemon','lime'],['lemon','lime','chanh']),
 ('quýt',['quýt','mandarin orange','tangerine'],['mandarin','tangerine','quýt']),
 ('quả cam|nước cam|ép cam',['cam','nước cam','orange'],['orange','citrus','cam']),
 ('nước ép|máy ép',['nước ép','fruit juice','juicer'],['juice','juicer','nước ép']),
 ('rau củ quả|rau củ|rau xanh|rau quả',['rau củ quả','rau xanh','vegetables'],['vegetable','greens','rau củ','rau xanh']),
 ('trái cây|hoa quả',['trái cây','hoa quả','fruits'],['fruit','trái cây','hoa quả']),
 ('các loại hạt|hạt dinh dưỡng',['các loại hạt','mixed nuts'],['nuts','nut mix','hạt dinh dưỡng']),
 # Exact organs and activities precede their broader topic families.
 ('não|trí não|bộ não',['não bộ','brain anatomy','human brain'],['brain','cerebral','não']),
 ('da|làn da|da mặt|chăm sóc da',['làn da','skin','skincare'],['skin','skincare','làn da','da mặt']),
 ('tim|trái tim|tim mạch|nhịp tim',['tim','heart anatomy','heartbeat'],['heart','cardiac','tim']),
 ('dạ dày',['dạ dày','stomach anatomy'],['stomach','dạ dày']),
 ('đường ruột|ruột|niêm mạc|hệ vi sinh',['đường ruột','intestines','gut microbiome'],['intestine','gut','microbiome','ruột']),
 ('đi bộ',['người già đi bộ','walking','senior walking'],['walk','walking','đi bộ']),
 ('thái cực quyền|dưỡng sinh',['dưỡng sinh','tai chi'],['tai chi','qigong','dưỡng sinh','thái cực quyền']),
 ('thể dục|tập tại nhà|tập luyện',['người già thể dục','senior exercise','exercise'],['exercise','fitness','workout','thể dục','tập luyện']),
 ('đường huyết|tiểu đường|insulin|lượng đường|đường thấm|đường vào máu',['đường huyết','tiểu đường','blood sugar'],['glucose','blood sugar','diabetes','glucometer','insulin','đường huyết']),
 ('máu|mạch máu|tĩnh mạch|động mạch|hồng cầu|tuần hoàn',['mạch máu','máu','blood vessels'],['blood','artery','vessel','vein','circulation','máu','mạch']),
 ('tiêu hóa',['hệ tiêu hóa','digestive system'],['digestive','digestion','tiêu hóa']),
 ('đầy hơi|chướng bụng|đau bụng|bụng căng|bụ căng',['đau bụng','dạ dày','stomach'],['stomach','abdomen','belly','bụng']),
 ('gan',['gan','liver'],['liver','gan']),('thận',['thận','kidney'],['kidney','renal','thận']),
 ('nhón gót|kiễng|nâng gót|bắp chân|gân gót',['bài tập chân','bắp chân','nhón gót','leg exercise'],['leg','calf','calves','heel','foot','feet','bắp chân','chân']),
 ('ngủ|giấc ngủ|mất ngủ',['ngủ','người già ngủ','sleep'],['sleep','bed','ngủ','giường']),
 ('thức dậy|tỉnh giấc',['thức dậy','buổi sáng','waking up'],['wake','waking','morning','bed','thức dậy','buổi sáng']),
 ('đau lưng|thắt lưng',['đau lưng','lưng','back pain'],['back','spine','lưng']),
 ('đầu gối|xương khớp|đau khớp',['đầu gối','xương khớp','knee'],['knee','joint','đầu gối','khớp']),
 ('trà|thảo mộc|thảo dược',['trà','thảo dược','herbal tea'],['tea','herbal','herb','trà','thảo dược']),
]

def topic_for(text):
    text=unicodedata.normalize('NFC',text.lower())
    return next((topic for topic in TOPICS if any(re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',text) for w in topic[0].split('|'))),None)

def related_topic(scene):
    """Give the stock picker a simpler subject without replacing saved queries."""
    phrases = scene.get('queries', []) if scene.get('manual_queries') else scene.get('subjects') or scene.get('queries', [])
    for phrase in phrases:
        topic = topic_for(phrase)
        if not topic and phrase.isascii():
            text = norm(phrase)
            matches = [
                (len(term), item)
                for item in TOPICS
                for term in item[2]
                if term.isascii()
                and term not in {'back', 'bed', 'beet', 'blood', 'foot', 'leg', 'skin', 'vessel'}
                and re.search(r'(?<!\w)' + re.escape(term) + r'(?:s|es)?(?!\w)', text)
            ]
            if matches:
                topic = max(matches, key=lambda match: match[0])[1]
        if topic:
            _, queries, subjects = topic
            return dict(queries=queries, subjects=subjects)
    return None

def broaden(scene,context=''):
    direct=topic_for(scene.get('text',''))
    previous={norm(w) for w in scene.get('subjects',[])}
    topic=direct or topic_for(context) or next((t for t in TOPICS if previous.intersection(map(norm,t[2]))),None)
    if topic:
        _,queries,subjects=topic
        scene.update(queries=list(queries),subjects=list(subjects),positive=list(subjects),query_basis='chủ đề ngắn trong lời đọc' if direct else 'chủ đề ngắn theo ngữ cảnh')
    scene['topic_only']=True
    return scene

"""Short topic searches; actions are preferences rather than requirements."""
import re,unicodedata
from .core import norm

TOPICS=[
 ('quả cam|nước cam|ép cam',['cam','nước cam','orange'],['orange','citrus','cam']),
 ('nước ép|máy ép',['nước ép','trái cây','fruit juice'],['juice','fruit','juicer','nước ép','trái cây']),
 ('đường huyết|tiểu đường|insulin|lượng đường|đường thấm|đường vào máu',['đường huyết','tiểu đường','blood sugar'],['glucose','blood sugar','diabetes','glucometer','insulin','đường huyết']),
 ('máu|mạch máu|tĩnh mạch|động mạch|hồng cầu|tuần hoàn',['mạch máu','máu','blood vessels'],['blood','artery','vessel','vein','circulation','máu','mạch']),
 ('đường ruột|dạ dày|ruột|niêm mạc|hệ vi sinh|tiêu hóa',['dạ dày','đường ruột','tiêu hóa','digestive system'],['stomach','intestine','digestive','gut','microbiome','dạ dày','ruột','tiêu hóa']),
 ('đầy hơi|chướng bụng|đau bụng|bụng căng|bụ căng',['đau bụng','dạ dày','stomach'],['stomach','abdomen','belly','bụng']),
 ('gan',['gan','liver'],['liver','gan']),('thận',['thận','kidney'],['kidney','renal','thận']),
 ('trái tim|tim mạch|nhịp tim',['tim','tim mạch','heart'],['heart','cardiac','tim']),
 ('đu đủ',['đu đủ','papaya'],['papaya','đu đủ']),('chanh|quýt',['chanh','cam quýt','citrus'],['lemon','lime','citrus','orange','chanh','quýt']),
 ('rau xanh|rau củ',['rau xanh','rau củ','vegetables'],['vegetable','greens','salad','rau']),
 ('nhón gót|kiễng|nâng gót|bắp chân|gân gót',['bài tập chân','bắp chân','nhón gót','leg exercise'],['leg','calf','calves','heel','foot','feet','bắp chân','chân']),
 ('thể dục|tập tại nhà|dưỡng sinh|thái cực quyền|tập luyện',['người già thể dục','người cao tuổi tập luyện','senior exercise'],['exercise','fitness','stretch','yoga','tai chi','walking','thể dục','tập luyện','dưỡng sinh']),
 ('đi bộ',['người già đi bộ','người già thể dục','senior walking'],['walk','walking','exercise','đi bộ','thể dục']),
 ('ngủ|giấc ngủ|mất ngủ',['ngủ','người già ngủ','sleep'],['sleep','bed','ngủ','giường']),
 ('thức dậy|tỉnh giấc',['thức dậy','buổi sáng','waking up'],['wake','waking','morning','bed','thức dậy','buổi sáng']),
 ('đau lưng|thắt lưng',['đau lưng','lưng','back pain'],['back','spine','lưng']),
 ('đầu gối|xương khớp|đau khớp',['đầu gối','xương khớp','knee'],['knee','joint','đầu gối','khớp']),
 ('trà|thảo mộc|thảo dược',['trà','thảo dược','herbal tea'],['tea','herbal','herb','trà','thảo dược']),
]

def broaden(scene):
    text=unicodedata.normalize('NFC',scene.get('text','').lower())
    direct=next((topic for topic in TOPICS if any(re.search(r'(?<!\w)'+re.escape(w)+r'(?!\w)',text) for w in topic[0].split('|'))),None)
    previous={norm(w) for w in scene.get('subjects',[])}
    topic=direct or next((t for t in TOPICS if previous.intersection(map(norm,t[2]))),None)
    if topic:
        _,queries,subjects=topic
        scene.update(queries=list(queries),subjects=list(subjects),positive=list(subjects),query_basis='chủ đề ngắn trong lời đọc' if direct else 'chủ đề ngắn theo ngữ cảnh')
    scene['topic_only']=True
    return scene

from pptx import Presentation
p=Presentation('v124.pptx')
def runs(tf):
    for para in tf.paragraphs:
        for r in para.runs: yield r
n=0
for s in p.slides:
    for sh in s.shapes:
        tfs=[sh.text_frame] if sh.has_text_frame else []
        if sh.has_table: tfs=[c.text_frame for r in sh.table.rows for c in r.cells]
        for tf in tfs:
            for r in runs(tf):
                if '碰撞' in r.text: r.text=r.text.replace('碰撞率','拒絕率').replace('碰撞','拒絕');n+=1
    nt=s.notes_slide.notes_text_frame
    if '碰撞' in nt.text:
        t=nt.text.replace('碰撞率','拒絕率').replace('碰撞','拒絕')
        if t.startswith('老師質疑'):
            t='先說明名詞：我原本說的碰撞率改稱拒絕率，指前面已接受的包占走 contact 時段或 Buffer 後，這包找不到可行排程而被拒絕的比例，不是封包碰撞。'+t
        nt.text=t;n+=1
print(n)
p.save('v125.pptx')

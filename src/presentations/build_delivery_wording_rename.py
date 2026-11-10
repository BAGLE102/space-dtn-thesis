from pptx import Presentation
NOTE_DEF='先說明名詞：DTN 文獻的主要指標是送達率，我們也用送達率。未送達的包都是在規劃階段被拒絕，也就是前面已接受的包占走 contact 時段或 Buffer 後，這包找不到可行排程；被拒絕的比例就是 1 減送達率。我原本說的碰撞率就是這個比例，不是封包碰撞。'
S={
 '3 MB 的拒絕率（原稱碰撞率）為什麼這麼高？':'3 MB 的送達率為什麼這麼低？',
 '問題一：3 MB 拒絕率為什麼這麼高':'問題一：3 MB 送達率為什麼這麼低',
 '拒絕率 = 被拒絕包數 ÷ 總包數（前面的包占走 contact 時段或 Buffer 後，找不到可行排程）':'未送達的包都是規劃時被拒絕：前面的包占走 contact 時段或 Buffer，找不到可行排程',
 '把產生時間拉開或 Buffer 加大，拒絕率就大幅下降。':'把產生時間拉開或 Buffer 加大，送達率就大幅上升。',
 '3 MB 拒絕率為什麼高':'3 MB 送達率為什麼低',
 '沒有找到計算錯誤；拒絕率高主要來自負載設定：全部包集中在前 600 秒產生。':'沒有找到計算錯誤；送達率低主要來自負載設定：全部包集中在前 600 秒產生。',
 '拒絕率 = 被拒絕包數／總包數；k=1 原設定為 9～53%。失敗位置：來源 35%、中繼 54%、目的地 11%':'未送達 = 規劃時被拒絕；k=1 原設定送達率 47～91%。失敗位置：來源 35%、中繼 54%、目的地 11%',
 '拒絕率怎麼定義？負載多少合理？':'負載多少合理？',
 '被拒絕包數／總包數；600 秒內產生':'全部包在 600 秒內產生',
 'k=1 在 3 MB 時為 9～53%':'k=1 在 3 MB 時送達率 47～91%',
}
N=[('上次討論老師提了三個問題：3 MB 的拒絕率為什麼這麼高','上次討論老師提了三個問題：3 MB 的送達率為什麼這麼低'),
 ('先說明名詞：我原本說的碰撞率改稱拒絕率，指前面已接受的包占走 contact 時段或 Buffer 後，這包找不到可行排程而被拒絕的比例，不是封包碰撞。',NOTE_DEF),
 ('所以上限設成 3 MB，拒絕不可避免。','所以上限設成 3 MB，一定有包送不到。'),
 ('所以 3 MB 的拒絕率高是設定造成的','所以 3 MB 的送達率低是設定造成的'),
 ('老師質疑 3 MB 的拒絕率太高','老師質疑 3 MB 的送達率太低、碰撞太多'),
 ('拒絕率高是設定造成的。','送達率低是設定造成的。'),
 ('第七項：拒絕率目前定義為被拒絕的包占全部包的比例；全部包在前 600 秒產生，負載偏高，需要老師決定合理範圍。','第七項：全部包在前 600 秒產生，負載偏高，3 MB 時 k=1 送達率只有 47% 到 91%，需要老師決定合理的負載範圍。')]
def run(src,dst):
    p=Presentation(src);n=0
    for s in p.slides:
        for sh in s.shapes:
            tfs=[sh.text_frame] if sh.has_text_frame else ([c.text_frame for r in sh.table.rows for c in r.cells] if sh.has_table else [])
            for tf in tfs:
                if tf.text in S:
                    rs=[r for para in tf.paragraphs for r in para.runs];rs[0].text=S[tf.text]
                    for r in rs[1:]:r.text=''
                    n+=1
        nt=s.notes_slide.notes_text_frame;t=nt.text
        for a,b in N:t=t.replace(a,b)
        if t!=nt.text:nt.text=t;n+=1
        assert '拒絕率' not in nt.text,nt.text
    p.save(dst);print(dst,n)
run('three_questions_v1.1.pptx','three_questions_v1.2.pptx')
run('v125.pptx','v126.pptx')

from pptx import Presentation
from pptx.dml.color import RGBColor as RGB
p=Presentation('three_questions_v1.pptx')
BLUE={'3932A8','187A3E','B03A2E'}
n=0
def fix(tf):
    global n
    for para in tf.paragraphs:
        for r in para.runs:
            c=r.font.color
            if c and c.type is not None and str(c.rgb) in BLUE:
                c.rgb=RGB.from_string('222222');n+=1
for s in p.slides:
    for sh in s.shapes:
        if sh.has_text_frame:fix(sh.text_frame)
        if sh.has_table:
            for row in sh.table.rows:
                for cell in row.cells:fix(cell.text_frame)
print(n)
p.save('three_questions_v1.1.pptx')

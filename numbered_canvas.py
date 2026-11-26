from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

class NumberedCanvas(canvas.Canvas):
    def __init__(self,*args,**kwargs ):
        super().__init__(*args,**kwargs)
        self._saved_page_states=[]
        self._margin_y=12*mm
        self._margin_x=10*mm
    
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage() # type: ignore


    
    def save(self):
        num_pages=len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    def draw_page_number(self,page_count):
        self.saveState()
        self.setFont("Helvetica",9)
        self.setFillColor(colors.HexColor("#718096"))
        page_width,_=A4
        footer_y=30

        self.drawString(self._margin_x,footer_y,"╤ Meter data Analysis report")
        page_text=f"Page {self._pageNumber} of {page_count}" # type: ignore
        self.drawString(page_width-(self._margin_x*2.9),footer_y,page_text)


        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(self._margin_x,footer_y+12,page_width-self._margin_x,footer_y+12)

        self.restoreState()

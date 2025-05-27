import  pyautogui as pag

x,y = pag.position()
print(x,y)

pos = pag.position()
print(pos)

pag.moveTo(0,0)
pag.moveRel(1,0)
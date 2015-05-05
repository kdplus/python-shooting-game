# -*- coding: cp936 -*-
import pygame
import math
from random import *
import pygame
from pygame.locals import *
from sys import *
from gameobjects.vector2 import Vector2

pygame.init()
pygame.mixer.init()
width,height=640,480
keys=[False,False,False,False,False,False]
playerpos=Vector2(100,100)
screen=pygame.display.set_mode((width,height))
pygame.display.set_caption("RABBITvsMOUSE")
arrows=[]
healthvalue=194
key_direction=Vector2(0,0)
clock=pygame.time.Clock()
clock2=pygame.time.Clock()
time_passed_seconds2=0
player_speed=300.
bullet_speed=800.
go=1

#载入音乐
hit=pygame.mixer.Sound("resources/audio/explode.wav")
enemy=pygame.mixer.Sound("resources/audio/enemy.wav")
shoot=pygame.mixer.Sound("resources/audio/shoot.wav")
hit.set_volume(0.05)
enemy.set_volume(0.05)
shoot.set_volume(0.05)
pygame.mixer.music.load("resources/audio/bgm.mp3")
pygame.mixer.music.play(-1,0.0)
pygame.mixer.music.set_volume(0.25)
#载入图片
player=pygame.image.load("resources/images/dude.png")
grass=pygame.image.load("resources/images/map.png")
arrow=pygame.image.load("resources/images/bb.png")
impimg=pygame.image.load("resources/images/199_1.png")
bossimg=pygame.image.load("resources/images/199_2.png")
dead=pygame.image.load("resources/images/dead.png")
you_win=pygame.image.load("resources/images/you_win.png")

#实体类以及状态机
class State(object):
    def __init__(self,name):
        self.name=name
    def do_actions(self):
        pass
    def check_conditions(self):
        pass
    def entry_actions(self):
        pass
    def exit_actions(self):
        pass


class ImpStateExploring(State):
    def __init__(self,imp):
        State.__init__(self,"exploring")
        self.imp=imp

    def random_destination(self):
        w,h=width,height
        self.imp.destination=Vector2(randint(0,w),randint(0,h))

    def do_actions(self):
        if randint(1,30)==1:
            self.random_destination()#控制决策频率
    def check_conditions(self):
        p1=self.imp.world.get_close_entity("p1",self.imp.location,200)
        if p1 is not None:
            if self.imp.location.get_distance_to(p1.location)<200.:
                self.imp.p1_id=p1.id
                return "hunting"
        return None
    
    def entry_actions(self):
        self.imp.speed=50.+randint(-10,10)
        #DEGUB print "exploring ",self.imp.speed
        self.random_destination()


class ImpStateHunting(State):
    def __init__(self,imp):
        State.__init__(self,"hunting")
        self.imp=imp
        self.got_kill=False
        
    def do_actions(self):
        p1=self.imp.world.get(self.imp.p1_id)
        if p1 is None:
            return
        self.imp.destination=p1.location
        if self.imp.location.get_distance_to(p1.location)<30.0:
            if randint(1,5)==1:
                p1.bitten()
                if p1.health<=0:
                    self.got_kill=True

    def check_conditions(self):
        if self.got_kill:
            return "exploring"
        p1=self.imp.world.get(self.imp.p1_id)
        if p1 is None:
            return "exploring"
        if p1.location.get_distance_to(self.imp.location)>200.0:
            return "exploring"
        return None
    def entry_actions(self):
        self.imp.speed=120.+randint(0,30)
        if self.imp.num==1:
            self.imp.speed+=70
        #DEGUB print "hunting ",self.imp.speed

    def exit_actions(self):
        self.got_kill=False
        

class StateMachine(object):
    #储存状态并负责转移状态执行状态
    def __init__(self):
        self.states={}
        self.active_state=None
    def add_state(self,state):
        self.states[state.name]=state
    def think(self):
        if self.active_state is None:
            return
        self.active_state.do_actions()
        new_state_name=self.active_state.check_conditions()
        if new_state_name is not None:
            self.set_state(new_state_name)
    def set_state(self,new_state_name):
        if self.active_state is not None:
            self.active_state.exit_actions()
        self.active_state=self.states[new_state_name]
        self.active_state.entry_actions()
        

class GameEntity(object):
    def __init__(self,world,name,image):
        self.world=world
        self.name=name
        self.image=image
        self.location=Vector2(0,0)
        self.destination=Vector2(0,0)
        self.speed=0.
        #大脑就是状态机类的
        self.brain=StateMachine()
        self.id=0
        self.num=0
        self.health=0
    def render(self,surface):
        x,y=self.location
        #w,h=self.image.get_size()
        surface.blit(self.image,(x,y))
    def process(self,time_passed):
        #让状态机来更新状态
        self.brain.think()
        if self.speed>0. and self.location!=self.destination:
            vec_to_destination=self.destination-self.location
            distance_to_destination=vec_to_destination.get_length()
            heading=vec_to_destination.get_normalized()
            travel_distance=min(distance_to_destination,time_passed*self.speed)
            self.location+=travel_distance*heading


class Imp(GameEntity):
    def __init__(self,world,image):

        GameEntity.__init__(self,world,"Imp",image)
        exploring_state=ImpStateExploring(self)
        hunting_state=ImpStateHunting(self)

        self.brain.add_state(exploring_state)
        self.brain.add_state(hunting_state)
        self.health=1

class Boss(Imp):
    def __init__(self,world,image):
        Imp.__init__(self,world,image)
        self.num=1
        self.health=5
        

class P1(GameEntity):
    def __init__(self,world,image):
        GameEntity.__init__(self,world,"p1",image)
        self.speed=300.
    def bitten(self):
        self.health-=2
    def render(self,surface):
        GameEntity.render(self,surface)
        x,y=self.location
        w,h=self.image.get_size()
        bar_x=x+15
        bar_y=y-h/3.0
        surface.fill((255,0,0),(bar_x,bar_y,25,4))
        surface.fill((0,255,0),(bar_x,bar_y,self.health/float(healthvalue)*25,4))
        
    
class World(object):
    def __init__(self):
        self.entities={}
        self.entity_id=0

    def add_entity(self,entity):
        self.entities[self.entity_id]=entity
        entity.id=self.entity_id
        self.entity_id+=1

    def remove_entity(self,entity):
        del self.entities[entity.id]

    def get(self,entity_id):
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None

    def process(self,time_passed):
        #根据时间更新全部存在world里面的实体的状态
        time_passed_seconds=time_passed/1000.0
        for entity in self.entities.values():
            entity.process(time_passed_seconds)

    def render(self,surface):
        screen.fill(0)
        #显示背景
        for x in range(width/grass.get_width()+1):
            for y in range(height/grass.get_height()+1):
                surface.blit(grass,(x*grass.get_width(),y*grass.get_height()))
        #显示所有实体
        for entity in self.entities.itervalues():
            entity.render(surface)

    def get_close_entity(self,name,location,range=100.):

        location=Vector2(*location)
        #寻找实体列表中指定物体中最近的，且在range范围内的
        for entity in self.entities.itervalues():
            if entity.name==name:
                distance=location.get_distance_to(entity.location)
                if distance<range:
                    return entity
        return None

world=World()
p=P1(world,player)
p.location=playerpos
p.health=194
world.add_entity(p)
roundnum=0
exitcode=0
#ROUND控制
for num in range(20,55,5):
    nownum=num
    for i in range(num):
        if i%5==0 :
            boss=Boss(world,bossimg)
            boss.location=Vector2(640,randint(0,height))
            boss.brain.set_state("exploring")
            world.add_entity(boss)
        else:
            imp=Imp(world,impimg)
            imp.location=Vector2(640,randint(0,height))
            imp.brain.set_state("exploring")
            world.add_entity(imp)
    roundnum+=1
            
    while nownum:
        screen.fill(0)
        #计时
        time_passed=clock.tick(30)
        time_passed_seconds=time_passed/1000.0
        #显示world
        world.process(time_passed)
        world.render(screen)
        #显示计时器&round数
        font=pygame.font.Font(None,24)
        survivedtext = font.render(str((pygame.time.get_ticks())/60000)+":"+str((pygame.time.get_ticks())/1000%60).zfill(2), True, (0,0,0))
        textRect=survivedtext.get_rect()
        textRect.topright=[320,460]
        screen.blit(survivedtext,textRect)
        
        roundtext = font.render("ROUND %d!!!"%(roundnum),True,(200,100,100))
        textRect=roundtext.get_rect()
        textRect.topright=[360,440]
        screen.blit(roundtext,textRect)
        
        #旋转player计算位置并显示s
        angle=math.atan2(key_direction.y,key_direction.x)
        playerrot=pygame.transform.rotate(player,360-angle*57.29)
        playerpos+=go*key_direction*player_speed*time_passed_seconds
        if playerpos.x<0:
            playerpos.x=0
        if playerpos.x>640:
            playerpos.x=640
        if playerpos.y<0:
            playerpos.y=0
        if playerpos.y>480:
            playerpos.y=480
        playerpos1=Vector2(playerpos.x,playerpos.y)
        #playerpos=playerpos1
        #screen.blit(playerrot,playerpos1)
        #print playerpos-playerpos1
        p.image=playerrot
        p.location=playerpos1
        
        #计算显示子弹的位置
        for bullet in arrows:
            index=0
            velx=math.cos(bullet[0])*bullet_speed*time_passed_seconds
            vely=math.sin(bullet[0])*bullet_speed*time_passed_seconds
            bullet[1]+=velx
            bullet[2]+=vely
            if bullet[1]<-64 or bullet[1]>640 or bullet[2]<-64 or bullet[2]>480:
                arrows.pop(index)
            index+=1
            for projectile in arrows:
                arrow1=pygame.transform.rotate(arrow,360-projectile[0]*57.29)
                screen.blit(arrow1,(projectile[1],projectile[2]))

        #子弹和IMP交集
        delist={}
        t=0
        for entity in world.entities.itervalues():
            if entity.name=="Imp":
                imprect=pygame.Rect(entity.image.get_rect())
                imprect.top=entity.location.y
                imprect.left=entity.location.x
                
                index1=0
                for bullet in arrows:
                    bullrect=pygame.Rect(arrow.get_rect())
                    bullrect.left=bullet[1]
                    bullrect.top=bullet[2]
                    if imprect.colliderect(bullrect):
                        enemy.play()
                        arrows.pop(index1)
                        index1+=1
                        #print entity.id
                        entity.health-=1
                        if entity.health==0:
                            delist[t]=entity
                            t+=1
                        #print entity
                        break
                        #print world.entities[entity.id]
        for i in range(0,t):
            if delist[i] is not None:
                world.remove_entity(delist[i])
        nownum-=t
        #print nownum
        '''
        if badtimer==0:
            badguys.append([640,randint(50,430),0])
            badtimer=100-(badtimer1*2)
            if badtimer1>=35:
                badtimer1=35
            else:
                badtimer1+=5
        index=0
        
        for badguy in badguys:
            if badguy[0]<-64:
                badguys.pop(index)
            badguy[2]=math.atan2((playerpos1[1]+32)-badguy[1],(playerpos1[0]+26)-badguy[0])
            velx=math.cos(badguy[2])*0.3
            vely=math.sin(badguy[2])*0.3
            badguy[0]+=velx
            badguy[1]+=vely
            
            badrect=pygame.Rect(badguyimg.get_rect())
            badrect.top=badguy[1]
            badrect.left=badguy[0]
            
            index1=0
            playerrect=pygame.Rect(player.get_rect())
            playerrect.left=playerpos1[0]
            playerrect.top=playerpos1[1]
            #碰到怪减血
            while(badrect.colliderect(playerrect)):
                hit.play()
                p.health-=randint(0,1)
                badguy[0]-=velx*100
                badguy[1]-=vely*100
                badrect.top=badguy[1]
                badrect.left=badguy[0]
                
                
            for bullet in arrows:
                bullrect=pygame.Rect(arrow.get_rect())
                bullrect.left=bullet[1]
                bullrect.top=bullet[2]
                if badrect.colliderect(bullrect):
                    enemy.play()
                    acc[0]+=1
                    badguys.pop(index)
                    arrows.pop(index1)
                index1+=1
            index+=1
            
        for badguy in badguys:
            badguyrot=pygame.transform.rotate(badguyimg,180-badguy[2]*57.29)
            badguypos1=(badguy[0]-badguyrot.get_rect().width/2,badguy[1]-badguyrot.get_rect().height/2)
            screen.blit(badguyrot,badguypos1)
            #screen.blit(badguyimg,(badguy[0],badguy[1]))
   
        for entity in world.entities.itervalues():
            if entity.name=="Imp":
                #print entity.brain.active_state.name
                if entity.brain.active_state.name=='hunting':
                    #print "in"
                    angle=math.atan2(entity.destination.y,entity.destination.x)
                    improt=pygame.transform.rotate(badguyimg,180-angle*57.29)
                    w,h=0,0
                    imppos1=Vector2(entity.location.x-w/2,entity.location.y-h/2)
                    #playerpos=playerpos1
                    #screen.blit(playerrot,playerpos1)
                    #print playerpos-playerpos1
                    entity.image=improt
                    entity.location=imppos1
                    print angle*57.29
                else:
                    entity.image=badguyimg
                   
        for badguy in badguys:
            
            badguyrot=pygame.transform.rotate(badguyimg,180-badguy[2]*57.29)
            badguypos1=(badguy[0]-badguyrot.get_rect().width/2,badguy[1]-badguyrot.get_rect().height/2)
            screen.blit(badguyrot,badguypos1)
            #screen.blit(badguyimg,(badguy[0],badguy[1])'''
        #更新显示
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                quit()
                exit(0)
            if event.type==pygame.KEYDOWN:
                if event.key==K_w:
                    keys[0]=True
                elif event.key==K_a:
                    keys[1]=True
                elif event.key==K_s:
                    keys[2]=True
                elif event.key==K_d:
                    keys[3]=True
                elif event.key==K_j:
                    keys[4]=True
                elif event.key==K_k:
                    keys[5]=True
            if event.type==pygame.KEYUP:
                if event.key==pygame.K_w:
                    keys[0]=False
                elif event.key==pygame.K_a:
                    keys[1]=False
                elif event.key==pygame.K_s:
                    keys[2]=False
                elif event.key==pygame.K_d:
                    keys[3]=False
                elif event.key==K_j:
                    keys[4]=False
                elif event.key==K_k:
                    keys[5]=False
            pressed_keys=pygame.key.get_pressed()
            
        #射出子弹，并控制子弹间隔速度
        if pressed_keys[K_j]:
            time_passed2=clock2.tick(30)
            time_passed_seconds2+=time_passed2/1000.0
            if time_passed_seconds2 >0.3 :
                shoot.play()
                arrows.append([angle,playerpos1.x+32,playerpos1.y+32])
                time_passed_seconds2=0
        #更新p1方向
        if not(keys[0]==False and keys[2]==False and keys[1]==False and keys[3]==False):
            go=1
            key_direction=Vector2(0,0)
        else:
            go=0
        if keys[0]:
            key_direction.y-=1
        elif keys[2]:
            key_direction.y+=1
        if keys[1]:
            key_direction.x-=1
        elif keys[3]:
            key_direction.x+=1
        key_direction.normalize()
        if p.health<=0 :
            exitcode=1
            break
    #无血退出    
    if p.health<=0 :
        exitcode=1
        break
        

#退出机制
if exitcode==1:
    pygame.font.init()
    font=pygame.font.Font(None,40)
    text=font.render("survtime: "+str((pygame.time.get_ticks())/60000)+":"+str((pygame.time.get_ticks())/1000%60).zfill(2),True,(255,0,0))
    textRect=text.get_rect()
    textRect.centerx=screen.get_rect().centerx
    textRect.centery=screen.get_rect().centery+24
    screen.blit(dead,(0,0))
    screen.blit(text,(220,230))
else:
    pygame.font.init()
    font=pygame.font.Font(None,24)
    screen.blit(you_win,(0,0))
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit(0)
    pygame.display.flip()

        
            
            
    

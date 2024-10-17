import utm
import numpy as np
import pandas as pd
import math

def hata(gw_height, sf):
    sens_height = 1
    # represents Spreading Factor Tolerances for Path Loss in dB
    plrange = [131, 134, 137, 140, 141, 144]
    distance = 10 ** (-(69.55 + 76.872985 - 13.82 * math.log10(gw_height) - 3.2 * (math.log10(
        11.75 * sens_height) ** 2) + 4.97 - plrange[sf - 7]) / (44.9 - 6.55 * math.log10(gw_height)))
    return distance * 1000

def uniform(bb,amount):
    coords=[]
    ysteps=np.linspace(bb[2],bb[3],dtype=float,num=int(math.sqrt(amount)))
    for y in ysteps:
        xsteps=np.linspace(bb[0],bb[1],dtype=float,num=int(math.sqrt(amount)))
        for x in xsteps:
            coords.append([x,y])
    return coords

def random_square(bb,amount):
    return([[(np.random.rand()*(bb[1]-bb[0]))+bb[0],(np.random.rand()*(bb[3]-bb[2]))+bb[2]] for i in range(amount)])

def circle(bb,amount):
    coords=[]
    for i in range(amount):
        r=math.sqrt(np.random.rand())
        u=np.random.rand()*2*math.pi
        x=((r*math.cos(u)+1)*0.5)
        y=((r*math.sin(u)+1)*0.5)
        coords.append([x*(bb[1]-bb[0])+bb[0],(y*(bb[3]-bb[2]))+bb[2]])
    return(coords)

def wrong_circle(bb,amount):
    coords=[]
    for i in range(amount):
        r=np.random.rand()
        u=np.random.rand()*2*math.pi
        x=((r*math.cos(u)+1)*0.5)
        y=((r*math.sin(u)+1)*0.5)
        coords.append([x*(bb[1]-bb[0])+bb[0],(y*(bb[3]-bb[2]))+bb[2]])
    return(coords)

def export(coords,filename):
    output={"x": [], "y": []}
    for i in coords:
        output["x"].append(i[0])
        output["y"].append(i[1])
        #print(output)
    df=pd.DataFrame.from_dict(output)
    df.to_csv(filename,index=False,header=False)


"POLYGON ((9.7905947 49.7762708, 9.8596027 49.7763262, 9.8579719 49.8203154, 9.790509 49.8203154, 9.7905947 49.7762708))"

if __name__ == "__main__":
    range_steps = 100
    bb1=utm.from_latlon(49.7762708,9.7905947)
    bb2=utm.from_latlon(49.7763262,9.8596027)
    bb3=utm.from_latlon(49.8203154,9.8579719)
    bb4=utm.from_latlon(49.8203154,9.790509)
    bb=[bb1,bb2,bb3,bb4]
    minx=float('inf')
    miny=float('inf')
    maxx=0
    maxy=0
    for curr in bb:
        if(curr[0]<minx):
            minx=curr[0]
        if(curr[1]<miny):
            miny=curr[1]
        if(curr[0]>maxx):
            maxx=curr[0]
        if(curr[1]>maxy):
            maxy=curr[1]
    bb=[minx,maxx,miny,maxy]
    bb[1]=bb[0]+1.8*hata(15,12)
    bb[3]=bb[2]+1.8*hata(15,12)
    for i in range(int(1.8*hata(15,12)),int(1.8*hata(15,7)),-100):
        export(circle(bb,700),'sensors_circle_'+str(i)+'.csv')
        bb[0] += range_steps
        bb[1] -= range_steps
        bb[2] += range_steps
        bb[3] -= range_steps
        #export(circle(bb,10000),'sensors_circle_'+str(i)+'.csv')
        #export(random_square(bb,5000),'sensors_random_square_'+str(i)+'.csv')
    #export(uniform(bb,5000),'sensors_uniform.csv')

'''
Date: 2021-07-18 14:44:24
LastEditors: chenfa
LastEditTime: 2021-07-19 11:38:46
'''

import os
import sys
import wget

import pandas as pd 

import matplotlib.pyplot as plt 
from PIL import Image
from astropy.coordinates import FK5
from astropy.coordinates import SkyCoord

from urllib.error import ContentTooShortError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# from concurrent.futures import ProcessPoolExecutor
# import multiprocessing


def get_sources(fid: str) -> pd.DataFrame:
    raw = pd.read_excel(fid, usecols=list(range(9))+[11, 12], dtype={
        'order':    int, 
        'RA1':      int,
        'RA2':      int,
        'RA3':      float,
        'De1':      int,
        'De2':      int,
        'De3':      float,
        'z':        float, 
        'theta':    float, 
        'alpha':    float, 
        'Counterpart':  str
    })
    return raw


def get_catalog(fid: str) -> list:
    f = open(fid, 'r')
    data = list(map(lambda l: [
        l[9:19],    # J2000 name
        l[122:129], # redshift from NED or literature
        l[130:137], # redshift from SIMBAD
        l[138:145]  # redshift from SDSS
        ], f.readlines()))
    return data


def image_finder(source: pd.Series, source_id: int =None) -> None:
    # change coord system from B1950 to J2000
    coord_B1950 = SkyCoord(
        '%3dh%2dm%4.1fs'%(source['RA1'], source['RA2'], source['RA3']), 
        '%4dd%2dm%2ds'%(source['De1'], source['De2'], source['De3']), 
        frame=FK5, equinox='B1950'
        )
    coord_J2000 = coord_B1950.transform_to(FK5(equinox='J2000'))
    ra, dec = coord_J2000.ra.hms, coord_J2000.dec.dms
    ra = (ra[0], abs(ra[1]), abs(ra[2]))
    dec = (dec[0], abs(dec[1]), abs(dec[2]))
    # catalog with redshift
    redcat = get_catalog('./ocars.txt')
    # start web driver
    driver = webdriver.Firefox()
    driver.get('http://astrogeo.org/vlbi_images/')
    assert "Astrogeo" in driver.title
    ra_input_box = driver.find_element_by_name('source_coordinate_ra')
    dec_input_box = driver.find_element_by_name('source_coordinate_dec')
    ra_input_box.clear()
    ra_input_box.send_keys("%02d_%02d_%04.1f"%(ra[0], ra[1], ra[2]))
    dec_input_box.clear()
    dec_input_box.send_keys("%03d_%02d_%02d"%(dec[0], dec[1], dec[2]))
    dec_input_box.send_keys(Keys.RETURN)
    driver.implicitly_wait(6)
    # set-up figure
    fig, axs = plt.subplots(3, 5, figsize=(32, 24), dpi=300)
    fig.subplots_adjust(wspace=0, hspace=0)
    for i in range(len(axs)):
        for j in range(len(axs[0])):
            axs[i, j].set_xticks([])
            axs[i, j].get_xaxis().set_visible(False)
            axs[i, j].set_yticks([])
            axs[i, j].get_yaxis().set_visible(False)
            axs[i, j].spines['top'].set_visible(False)
            axs[i, j].spines['bottom'].set_visible(False)
            axs[i, j].spines['left'].set_visible(False)
            axs[i, j].spines['right'].set_visible(False)
    # get objects from which queried
    objs = list(map(lambda i: driver.find_element_by_xpath('/html/body/table/tbody/tr[%d]/td[3]/tt/a'%(i+2)), range(5)))
    objdists = list(map(lambda i: driver.find_element_by_xpath('/html/body/table/tbody/tr[%d]/td[2]/tt'%(i+2)).text, range(5)))
    for objid, obj in enumerate(objs):
        objurl = obj.get_attribute('href')
        driver.execute_script('window.open("%s")'%objurl)
        driver.switch_to_window(driver.window_handles[1])
        driver.implicitly_wait(6)
        objname = driver.find_element_by_xpath('/html/body/center/tt/big/b').text
        objdist = objdists[objid]
        # plot 3 (at most) images for single source
        objimgsnum = len(driver.find_elements_by_xpath('/html/body/p/table/tbody/tr[@valign="TOP"]'))
        objobss = []
        # BFS img url, try best to drew 3 pictures
        for drawid in range(min(3, objimgsnum)):
            objobs = []
            imgcolnum = len(driver.find_elements_by_xpath('/html/body/p/table/tbody/tr[%d]/td'%(3+objimgsnum-drawid)))
            imgsubcolnum = len(driver.find_elements_by_xpath('/html/body/p/table/tbody/tr[%d]/td[%d]/tt/a'%(3+objimgsnum-drawid, imgcolnum-1)))
            for cellid in range((imgsubcolnum+3) // 4):
                objobs.append(driver.find_element_by_xpath('/html/body/p/table/tbody/tr[%d]/td[%d]/tt/a[%d]'%(3+objimgsnum-drawid, imgcolnum-1, cellid*4+1)).get_attribute('href'))
            if objobs:
                objobss.append(objobs)
        img_drew = 0
        while objobss and img_drew < 3:
            objobs = objobss.pop(0)
            imgurl = objobs.pop(0)
            if objobs:
                objobss.append(objobs)
            imgname = imgurl.split('/')[-1]
            imgpath = './sources/%s'%imgname
            imgpath_eps = imgpath[:-3] + '.eps'
            assert imgpath.split('.')[-1].lower() == 'ps'
            if not os.path.exists(imgpath_eps):
                try:
                    wget.download(imgurl, out=imgpath)
                except ContentTooShortError:
                    try: 
                        wget.download(imgurl, out=imgpath)
                    except:
                        print('failed to download %s. skipped!'%imgurl)
                        continue
                # using gostscript to change ps to eps, then delete ps file
                # PIL cannot deal with .ps format file downloaded here
                os.system('gs -o %s -sDEVICE=eps2write %s'%(imgpath_eps, imgpath))
                os.remove(imgpath)
            # plot eps on figure
            with Image.open(imgpath_eps) as img:
                axs[img_drew, objid].imshow(img)
                img_drew += 1
        # add source info to the title
        radec_B1950 = '%3dh%2dm%4.1fs %4dd%2dm%2ds'%(
            source['RA1'], source['RA2'], source['RA3'], 
            source['De1'], source['De2'], source['De3'])
        radec_J2000 = coord_J2000.to_string(style='hmsdms')
        fig.suptitle('order=%4d z=%6.4f theta=%6.4f alpha=%6.4f %s\n%s (B1950)    %s (J2000)'%(
            source['order'], source['z'], source['theta'], source['alpha'], 
            source['Counterpart'], radec_B1950, radec_J2000
        ))
        # query redshift of this object
        obj_redcat_matched = list(filter(lambda l: l[0] == objname, redcat))
        if len(obj_redcat_matched) == 0:
            print('No redshift matched with %s!'%objname)
            obj_redinfo = ['', '', '']
        else:
            obj_redinfo = obj_redcat_matched[0][1:]
        # add title for each column
        axs[0, objid].set_title('id = %s  dist = %s\nz = %s / %s / %s'%(objname, objdist, obj_redinfo[0], obj_redinfo[1], obj_redinfo[2]))
        # close this window and switch to the former one
        driver.close()
        driver.switch_to_window(driver.window_handles[0])
    # close browser
    driver.close()
    # save figure
    # plt.tight_layout()
    if source_id == None:
        plt.savefig('./results/o%04d.png'%(source['order']))
    else:
        plt.savefig('./results/%04d_o%04d.png'%(source_id, source['order']))
    plt.close()
    pass


def main(sysarg: list) -> None:
    if not os.path.exists('./sources'):
        os.mkdir('./sources')
    if not os.path.exists('./results'):
        os.mkdir('./results')
    sources = get_sources('./613compact.xlsx')
    rownum = sources.shape[0]
    job_range = [0, rownum] # [start, end) starts from 0
    # check commandline args
    if sysarg:
        if len(sysarg) == 2:
            if int(sysarg[0]) != -1:
                job_range[0] = int(sysarg[0])
            if int(sysarg[1]) != -1:
                job_range[1] = int(sysarg[1])
        else:
            print("""Usage: 
    python QuasarFindingHelper.py                     (Default as [start, end))
    python QuasarFindingHelper.py <start_id> <end_id> (Use `-1` for default, id starts from 0)""")
            sys.exit(0)
    assert job_range[1] > job_range[0]
    print(sources[job_range[0]:job_range[1]])
    for sid, source in sources[job_range[0]:job_range[1]].iterrows():
        image_finder(source, sid)
    pass


if __name__ == '__main__':
    main(sys.argv[1:])
from db.dbWrapper import DbWrapper
from walkerArgs import parseArgs
import os, glob
from shutil import copyfile

args = parseArgs()
dbWrapper = DbWrapper(str(args.db_method), str(args.dbip), args.dbport, args.dbusername, args.dbpassword, args.dbname, args.timezone)


def main():
    print ''
    print 'If you want to insert a Gymhash to your Database, just take the File from Unknown Folder starting with *gym_crop* '
    print 'and copy the last part of the Filename.'
    print ''
    print 'f.e. 1_gym_crop_55.747355_99.163981_1536177248.96_45b5939252c695a9.jpg - the Hash is 45b5939252c695a9 '
    print ''
    print 'Additionally you need the gym_id or fort_id (rm or monocle)'
    print ''

    hash = raw_input("Enter Hash Value from Filename: ")
   
    gym = raw_input("Enter Gym / Fort ID: ")

        
    print ''
    if hash and gym:
        if dbWrapper.insertHash(hash, 'gym', gym, '999'):
            print 'Hash added - the Gym should now be recognized.'
            
            for file in glob.glob("www_hash/unkgym_*" + str(hash) + ".jpg"):
                copyfile(file, 'www_hash/gym_0_0_' + str(hash) + '.jpg')
                os.remove(file)
            
        else:
            print 'something went wrong ....'
    else:
        print 'Empty input - start again ....'
    
    print ''

if __name__ == '__main__':
    main()
from django.core.management.base import BaseCommand, CommandError
from django.db.models.base import ObjectDoesNotExist
from book.models import Author, Book, Genre, Publisher
from registration.models import MyUser, BookRating
from django.contrib.auth.models import User
from django.conf import settings
import os
import platform
import csv
import random

class Command(BaseCommand):
    help = "Download data to database from specified path"
    showWarnings = True
    showErrors = True

    def add_arguments(self, parser):
        parser.add_argument('data_path', type=str, help="setting path to .csv files")
        parser.add_argument('--books_number', '-bn', dest="BN", type=int,
                            required=False, help='first BN rows of book.csv file to be loaded to database')
        parser.add_argument('--users_number', '-un', dest='UN', type=int,
                            required=False, help='set number of users to be created')
        parser.add_argument('--no-warnings', action='store_true', dest='nowarnings',
                            required=False, help='suppress warnings')
        parser.add_argument('--no-error-messages', action='store_true', dest='noerrormessages',
                            required=False, help='suppress error messages')

    def handle(self, *args, **options):
        necessaryFiles = {'books.csv':'', 'book_tags.csv':'', 'ratings.csv':'', 'tags.csv':'', 'to_read.csv':''}
        path = options['data_path']
        if not os.path.exists(path):
            self.error("Path {:s} does not exist".format(path))
            return
        if not os.path.isdir(path):
            self.error("Path {:s} have to be a directory".format(path))
            return
        root = []
        files = []
        for rt, dr, fl in os.walk(path):
             root = rt; files = fl; break
        for fl in files:
            if fl in necessaryFiles.keys():
                necessaryFiles[fl] = os.path.join(root, fl)
        allOk = True
        for k,v in necessaryFiles.items():
            if v == '':
                allOk = False
                self.stdout.write("File {:14s} is missing".format(k))
        if not allOk:
            self.error("There are missing files")
        else:
            # tags means genres
            self.stdout.write("Collecting data from .csv files")
            self.booksInfo = list(csv.reader(open(necessaryFiles['books.csv'])    , delimiter=','))
            self.bookTags  = list(csv.reader(open(necessaryFiles['book_tags.csv']), delimiter=','))
            self.ratings   = list(csv.reader(open(necessaryFiles['ratings.csv'])  , delimiter=','))
            self.tags      = list(csv.reader(open(necessaryFiles['tags.csv'])     , delimiter=','))
            self.toRead    = list(csv.reader(open(necessaryFiles['to_read.csv'])  , delimiter=','))
            self.stdout.write("Done. Start uploading data to DB")

            if options['nowarnings']:
                self.showWarnings=False

            if options['noerrormessages']:
                self.showErrors = False

            booksNumber = len(self.booksInfo)
            if options['BN']:
                booksNumber = options['BN']
            if booksNumber > len(self.booksInfo):
                self.error("BN can't be bigger than {:d}".format(len(self.booksInfo)))
                return
            if booksNumber <= 0:
                self.error("BN must be positive and not 0")
                return

            usersNumber = int(self.toRead[len(self.toRead) - 1][0])
            if options['UN']:
                usersNumber = options['UN']
            if usersNumber <= 0:
                self.error("BN must be positive and not 0")
                return

            self.userCreation(usersNumber)
            self.bookLoading(booksNumber)
            self.toReadLoading(usersNumber)

    def userCreation(self, num):
        people = [
            ['Vasiaaa'      , 'Василий'   , 'Андреевич'      , 'M'],
            ['NastaciaP'    , 'Анастасия' , 'Петровна'       , 'F'],
            ['PetrI'        , 'Пётр'      , 'Иванович'       , 'M'],
            ['Daria228'     , 'Дарья'     , 'Павлова'        , 'F'],
            ['Rustan227'    , 'Рустан'    , 'Рафиков'        , 'M'],
            ['Irina226'     , 'Ирина'     , 'Селина'         , 'F'],
            ['Victor225'    , 'Виктор'    , 'Давыдов'        , 'M'],
            ['Polina224'    , 'Полина'    , 'Долгова'        , 'F'],
            ['SuperMacho353', 'Прокопий'  , 'Бурбонович'     , 'M'],
            ['KlavaiA'      , 'Клавдия'   , 'Анатольевна'    , 'F'],
            ['KollaiderBum' , 'Андрон'    , 'Алексеевич'     , 'M'],
            ['Anuta@'       , 'Анна'      , 'Нетирпимова'    , 'F'],
            ['SunLover'     , 'Макар'     , 'Загар'          , 'M'],
            ['LenaA'        , 'Елена'     , 'Андреева'       , 'F'],
            ['Diakon'       , 'Фиофан'    , 'Митрофанович'   , 'M'],
            ['AlexaN5'      , 'Александра', 'Федотовна'      , 'F'],
            ['GrishaA'      , 'Григорий'  , 'Анатольевич'    , 'M'],
            ['MariaO'       , 'Мария'     , 'Опатитова'      , 'F'],
            ['PoemWriter'   , 'Гвидон'    , 'ПлохоСРифмойВич', 'M'],
            ['GlaphiraP'    , 'Глафира'   , 'Панфиньишна'    , 'F'],
        ]

        superPassword="supersecretpass"
        start = 0
        end = num
        for i in range(0, num):
            man = random.choice(people)
            nage = random.randint(10, 95)
            nUserName = "{:s}_{:d}".format(man[0], i)
            nuser = User(username=nUserName, first_name=man[1],
                            last_name=man[2], password="{:s}{:d}".format(superPassword, i))
            nuser.save()
            nMyUser = MyUser(user=nuser, age=nage, gender=man[3])
            nMyUser.save()
            start += 1
            self.progressBar(start, end, "Creation of users")

    def bookLoading(self, num):
        start = 1 # except first row
        end = num
        self.progressBar(start, end, "Books data uploading")
        btLen = len(self.bookTags) - 1
        rtLen = len(self.ratings) - 1
        for row in self.booksInfo[1:num+1]: # +1 because num+1-1=num
            bTitle  = str(row[10])
            bAuthor = str(row[7]).split(',')
            bRating = 0.0

            book = Book(id=row[1], title=bTitle, rating=bRating)
            smallImagePath = "/".join(row[22].split("/")[3:])
            book.smallImage = smallImagePath #os.path.join(settings.MEDIA_ROOT, smallImagePath)
            middleImagePath ="/".join(row[21].split("/")[3:])
            book.middleImage = middleImagePath  #os.path.join(settings.MEDIA_ROOT, middleImagePath)
            bigImagePathMas = row[21].split("/")[3:]
            bigImagePathMas[1] = bigImagePathMas[1].replace("m", "l")
            bigImagePath = "/".join(bigImagePathMas)
            book.bigImage = bigImagePath  #os.path.join(settings.MEDIA_ROOT, bigImagePath)

            book.save()
            ## Rating counting
            step = rtLen // 2
            maxIterations = rtLen // 2
            cnt = 0
            i = 1
            up = False
            down = False
            while not up and not down and cnt < maxIterations:
                cnt += 1
                if self.ratings[i][0] == row[1]:
                    caret = i
                    sum = 0.0
                    ratingCnt = 0.0

                    while caret > 1 and self.ratings[caret][0] == row[1]:
                        caret -= 1
                        curRating = float(self.ratings[caret][2])
                        userId = int(self.ratings[caret][1])
                        try:
                            curUser = User.objects.get(id=userId)
                            myUser = MyUser.objects.get(user=curUser)
                            br = BookRating(rtd_book=book, rating=curRating)
                            br.save()
                            curUser.save()
                            myUser.rated_books.add(br)
                            myUser.save()
                        except ObjectDoesNotExist:
                            self.warning("User with id = {:d} does not exist".format(userId))
                        sum += curRating
                        ratingCnt += 1.0

                    up = True
                    caret = i
                    while caret < rtLen and self.ratings[caret][0] == row[1]:
                        curRating = float(self.ratings[caret][2])
                        userId = int(self.ratings[caret][1])
                        try:
                            curUser = User.objects.get(id=userId)
                            myUser = MyUser.objects.get(user=curUser)
                            br = BookRating(rtd_book=book, rating=curRating)
                            br.save()
                            curUser.save()
                            myUser.rated_books.add(br)
                            myUser.save()
                        except ObjectDoesNotExist:
                            self.warning("User with id = {:d} does not exist".format(userId))
                        sum += curRating
                        ratingCnt += 1.0
                        caret += 1
                    down = True
                    bRating = sum / ratingCnt
                elif int(self.ratings[i][0]) > int(row[1]):
                    i -= step
                    step //= 2
                else:
                    i += step
                    step //= 2

            book.rating = bRating

            try:
                bDate = int(float(row[8]))
            except ValueError:
                bDate = 0
            book.date = bDate

            book.save()

            for auth in bAuthor:
                try:
                    a = Author.objects.get(name__exact=auth)
                except ObjectDoesNotExist:
                    a = Author(name=auth)
                    a.save()
                book.author.add(a)

            ## Genre setting
            step = btLen // 2
            maxIterations = btLen // 2
            cnt = 0
            i = 1
            up = False
            down = False
            while not up and not down and cnt < maxIterations:
                cnt += 1
                if self.bookTags[i][0] == row[1]:
                    caret = i
                    while caret > 1 and self.bookTags[caret][0] == row[1]:
                        caret -= 1
                        try:
                            g = Genre.objects.get(id=self.bookTags[caret][1])
                        except ObjectDoesNotExist:
                            g = Genre(name=self.tags[int(self.bookTags[caret][1])][1])
                            g.save()
                        book.genre.add(g)
                    up = True
                    caret = i
                    while caret < btLen and self.bookTags[caret][0] == row[1]:
                        try:
                            g = Genre.objects.get(id=self.bookTags[caret][1])
                        except ObjectDoesNotExist:
                            g = Genre(name=self.tags[int(self.bookTags[caret][1])][1])
                            g.save()
                        book.genre.add(g)
                        caret += 1
                    down = True
                elif int(self.bookTags[i][0]) > int(row[1]):
                    i -= step
                    step //= 2
                else:
                    i += step
                    step //= 2

            book.save()
            self.progressBar(start, end, "Books data uploading")
            start += 1

    def toReadLoading(self, num):
        start = 1
        end = num
        prev = ""
        for row in self.toRead[1:]:
            if prev != row[0]:
                prev = row[0]
                start += 1
            try:
                curUser = User.objects.get(id=int(row[0]))
                myUser = MyUser.objects.get(user=curUser)
                try:
                    book = Book.objects.get(id=int(row[1]))
                    myUser.to_read.add(book)
                    myUser.save()
                except ObjectDoesNotExist:
                    self.warning("Book with id {:s} doesn't exist".format(row[1]))
            except ObjectDoesNotExist:
                self.warning("User with id {:s} don't exist".format(row[0]))
            self.progressBar(start, end, "To_read data uploading")
            if start == num:
                break

    def error(self, msg):
        if self.showErrors:
            self.stdout.write("\n   Error: {:s}".format(msg))

    def warning(self, msg):
        if self.showWarnings:
            self.stdout.write("\n   Warning: {:s}".format(msg))

    def progressBar(self, cur, end, msg=""):
        done = 100 * cur // end
        percent = done
        done //= 2
        left = 50 - done
        ender = ""
        if left == 0:
            ender = "DONE\n"
        if platform.system() == 'Linux':
            self.stdout.write("\r{:3d}% \033[47;34m {:s}{:s} \033[0m {:s} {:s}".format(
                percent,'▪' * done, ' ' * left, msg, ender), ending='')
        else:
            self.stdout.write("\r{:3d}% [{:s}{:s}] {:s} {:s}".format(
                percent, '#' * done, ' ' * left, msg, ender), ending='')
        self.stdout.flush()

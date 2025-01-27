''' BLOCKNOTES - app
Author = florian.zah@gmail.com
------------------------------
STATUS: active

TO DO
[ ] - limit history to n registers
[ ] - create log file for error; can be a table in database; name: ErrorLog
[ ] - new function get_time_date; line 144?; used in (?more) than 2 places
[ ] - add new column in db: last_page: True/False to reopen at last page visited
    - alternative 1: create table last_page_visited: 
          option=lpv (lpv = last_page_visited) 
          value=Page2
    - alternative 2: create blocknotes.ini to store last page visited
    * work with function: save_at_closing (bind with this function)
[ ] - create a button and function to delete all pages + all content from db and 
      reset everithing to a single page: Page1. Function created in *Settings*.
'''

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import messagebox
import sqlite3
from sqlite3 import Error
from datetime import datetime as dt
from configparser import ConfigParser as cp
import re


class BlockNotes:
    def __init__(self, win):
        self.win = win
        self.win.protocol("WM_DELETE_WINDOW", self.save_at_closing)
        

        self.database = 'blocknotes.db'
        _table_name = 'Page'
        
        # SQLite
        config=cp()
        config.read('blocknotes.ini')
        self.last_page = config['DIVERSE']['last_tab']
        
        # Frame for buttons row
        fr = tk.Frame(self.win)
        fr.pack(fill='x')
        add_button = tk.Button(fr, text='[+]', fg='blue', command=self.add_new_page)
        add_button.pack(side='left')
        setting_button = tk.Button(fr, text='[*]', fg='black', command=self.set_settings)
        setting_button.pack(side='left')
        del_button = tk.Button(fr, text='[-]', fg='red', command=self.del_page)
        del_button.pack(side='right')

        # Notebook
        self.notebook = ttk.Notebook(self.win)
        self.notebook.pack(fill='both', expand=True)
        # Create Notebook pages (+ scrolledText - editors)
        self.create_refresh_tabs()
        self.notebook.bind("<<NotebookTabChanged>>", self.auto_save)


    def set_settings(self):
        """ Create a new tab/Page with name *Settings* where Settings class
        will be initialized. """
        # Create windows for settings
        ...



        
    def create_refresh_tabs(self):
        """ Create at beginnings tabs in notebook or
        Refreshes tabs after a tab is deleted. """
        self.pagini = self.connect_read_db(self.database)  # -> list ['Page1', 'Page2']
        for widget in self.notebook.winfo_children():
            widget.destroy()
        self.editori = {}
        for pag in self.pagini:
            self.editor = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, font=('Consolas', 10), width=50)
            self.notebook.add(self.editor, text=pag)
            self.editori[pag] = self.editor
            # Ia textul din ultima linie db
            self.curr.execute(f"SELECT content FROM {pag} ORDER BY id DESC LIMIT 1;")
            content = self.curr.fetchone()  # -> type: tuple;
            _c = content[0]  # _c continut
            # Insereaza textul in editoare
            if _c == None:
                _c = ''
                self.editor.insert('1.0', _c)
            else:
                self.editor.insert('1.0', _c)
        #print(self.editori)
        # Ia pagina initiala => .!notebook.!frame
        pagina_initiala = self.notebook.select()
        # Ia numele paginii initiale => Page1, type str
        self.pagina_initiala = self.notebook.tab(pagina_initiala, 'text')
        # Ia numele widget => .!notebook.!frame
        self.tabul_initial = self.win.nametowidget(pagina_initiala)
        
    def add_new_page(self):
        """ Add new page to BlockNotes. """
        # Add new page to BlockNotes
        last_page = list(self.editori.keys())[-1]
        pattern = r'(\D+)(\d+)'
        match = re.match(pattern, last_page)
        if match:
            word = match.group(1).strip()   # Get the word part
            number = match.group(2)         # Get the number part
        else:
            print('Page has no number')
            # scrie in log file
        nr = int(number) + 1 
        pag = f'Page{nr}'
        self.editor = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, font=('Consolas', 10), width=50)
        self.notebook.add(self.editor, text=pag)
        self.editori[pag] = self.editor
        #print(self.editori)

        # [ ] - Add new table in database
        self.create_new_database_page(pag)

    def create_new_database_page(self, pag):
        """ Create a new table in database with name=Page(n). """
         # Preia data si ora
        date, time = str(dt.now()).split(' ')
        _d = date.split('-')
        _date = f'{_d[2]}-{_d[1]}-{_d[0]}'  # 23.02.2024
        _time = time.split('.')[0]  # 16:23:57
        # Sqlite section
        sql = f"""
        CREATE TABLE IF NOT EXISTS {pag}(
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        content TEXT);"""
        sql_first_line = f"""
        INSERT INTO {pag} (date, time, content) 
        VALUES (?, ?, ?);"""
        self.curr.execute(sql)
        self.curr.execute(sql_first_line, (_date, _time, ""))
        self.conn.commit()


    def del_page(self):
        """ Delete current page from BlockNotes. 
        [ ] - replace Page with {Page(n)} in askyesno message."""
        # Take current tab/page and delete
        response = messagebox.askyesno('Confirm', 'Do you want to delete this Page?\nDeleting this page, the database content, \nfor this page will also be deleted.')
        if response:
            current_tab_index = self.notebook.index(self.notebook.select())
            pag = self.notebook.tab(current_tab_index, 'text')  # take name of tab for sqlite
            self.notebook.forget(current_tab_index) # delete tab
            # Delete current tab/page from database
            sql = f"DROP TABLE IF EXISTS {pag};"
            self.curr.execute(sql)
            self.conn.commit()
            
            # Delete from self.editori (dictionary of pages from db)
            del self.editori[pag]
            #print(self.editori)
            self.create_refresh_tabs()
        else:
            ...


    def auto_save(self, event):
        """ Auto-save at changing tab. """
        ed = self.editori[self.pagina_initiala]  # = class tkinter...; .!notebook.!frame...
        text = (ed.get('1.0', tk.END)).rstrip(' \n')
        # Ia ultima linie din tabelul Page[n]
        ultima_linie = (self.citeste_ultima_linie(self.pagina_initiala))[0].rstrip(' ')
        if text != ultima_linie:
            self.write_content_db(text, self.pagina_initiala)
        else:
            ...
        pagina_curenta = self.notebook.select()
        self.pagina_initiala = self.notebook.tab(pagina_curenta, 'text')
        # [ ] - creare pagina log

    
    def write_content_db(self, text, pag_initial):
        ''' Scrie in baza de date continutul la schimbarea tabului. '''
        # Preia data si ora
        date, time = str(dt.now()).split(' ')
        _d = date.split('-')
        _date = f'{_d[2]}-{_d[1]}-{_d[0]}'  # 23.02.2024
        _time = time.split('.')[0]  # 16:23:57

        # Scrie in tabel Pagina o noua inregistrare
        sql = f"INSERT INTO {pag_initial} (date, time, content) VALUES (?, ?, ?);"
        self.curr.execute(sql, (_date, _time, text))
        self.conn.commit()

    def connect_read_db(self, database):
        """ Connect and read database. """
        self.conn = sqlite3.connect(database)
        self.curr = self.conn.cursor()

        sql_tabele = """SELECT name FROM sqlite_master WHERE type='table';"""
        self.curr.execute(sql_tabele)
        tabele = self.curr.fetchall()  # -> list of tuples[('Page1',), ('Page2',), ('sqlite',)]
        # Ia doar tabelele pagini create de user
        pagini = []
        for i in tabele:
            if i[0][0].istitle():
                pagini.append(i[0])  # ['Page1', 'Pagex']
        # Return tables names from db; self.pagini; type: list
        return pagini

    def citeste_ultima_linie(self, tabel):
        """ Ia textul din ultima linie din DB, tabelul are numele paginii.
        Returneaza doar continutul (textul). """
        sql_content = f"SELECT content FROM {tabel} ORDER BY id DESC LIMIT 1; "
        self.curr.execute(sql_content)
        continut = self.curr.fetchone()
        return continut


    def save_at_closing(self):
        """ Save content in db at clicking x(    _ [] X)."""
        # Ia pagina currenta
        pagina_curenta = self.notebook.select()
        self.pagina_initiala = self.notebook.tab(pagina_curenta, 'text')
        # Ia editorul si scrisul din el
        ed = self.editori[self.pagina_initiala]  # = class tkinter...; .!notebook.!frame...
        text = (ed.get('1.0', tk.END)).rstrip(' \n')
        # Compara textele: in bd si din editor
        ultima_linie = (self.citeste_ultima_linie(self.pagina_initiala))[0].rstrip(' ')
        if text != ultima_linie:
            self.write_content_db(text, self.pagina_initiala)
        else:
            ...
        #pagina_curenta = self.notebook.select()
        #self.pagina_initiala = self.notebook.tab(pagina_curenta, 'text')
        # (Scrie in bd)
        self.win.destroy()

class Settings:
    def __init__(self):
        ...


        
        
def _test():
    '''Build app main windows.'''
    win = tk.Tk()
    win.title("BlockNotes")
    win.geometry('300x400+200+200')
    win.attributes('-topmost', 'true')
    win.configure(background='white')
    #win.iconbitmap("blocknotes.ico")
    app = BlockNotes(win)
    
    win.mainloop()
    
if __name__ == '__main__':
    _test()


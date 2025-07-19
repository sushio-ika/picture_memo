import random
import tkinter as tk
from tkinter import Menu, scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk

image_refs = []  # 画像参照を保持するリスト

# --- 関数定義 ---
def new_file():
    """新規ファイルを作成"""
    main_memo.delete(1.0, tk.END)
    main_memo.title("ピクメモ")

def open_file():
    """ファイルを開く"""
    filepath = filedialog.askopenfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]#拡張子設定
    )
    if filepath:
        with open(filepath, "r", encoding="utf-8") as file:
            main_memo.delete(1.0, tk.END)
            main_memo.insert(tk.END, file.read())
        form.title(f"{filepath}ピクメモ")

def save_file():
    """ファイルを保存"""
    filepath = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if filepath:
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(main_memo.get(1.0, tk.END))
        form.title(f"{filepath}ピクメモ")
        messagebox.showinfo("保存完了", "ファイルが正常に保存されました。")#メッセージ表示

def cut_text():
    """テキストを切り取り"""
    main_memo.event_generate("<<Cut>>")

def copy_text():
    """テキストをコピー"""
    main_memo.event_generate("<<Copy>>")

def paste_text():
    """テキストを貼り付け"""
    main_memo.event_generate("<<Paste>>")

def show_about():
    """バージョン情報を表示"""
    messagebox.showinfo(
        "ピクメモについて",
        "画像や動画を挿入できるメモ帳風アプリケーションです。\n"
        "Python と tkinter で作成しました。"
    )

def insert_image():
    filepath=filedialog.askopenfilename(
        title="画像を選択してください",
        filetypes=[("Image files","*.png *.jpg *.jpeg *.gif *.bmp")]
    )
    if not filepath:
        return

    try:
        original_image=Image.open(filepath)

        width=300
        height=int(original_image.height * width / original_image.width)
        resized_image=original_image.resize((width,height),Image.Resampling.LANCZOS)

        photo=ImageTk.PhotoImage(resized_image)

        main_memo.image_create(tk.INSERT,image=photo)

        image_refs.append(photo)  # 参照を保持してガーベジコレクションを防ぐ
    except Exception as e:
        print(f"画像ファイルの読み込み中にエラーが発生しました: {e}")


#def btn_click():
    #rm=random.randint(0,len(msg)-1)
    #moji_lbl["text"]=msg[rm]



#---GUI---
form=tk.Tk()#tk作成
form.title("ピクメモ")
form.minsize(1000,560)

menubar=Menu(form)
form.config(menu=menubar)

# 「ファイル」メニューの作成
file_menu=Menu(menubar,tearoff=0)
menubar.add_cascade(label="ファイル(F)",menu=file_menu)
file_menu.add_command(label="新規作成(N)", command=new_file)
file_menu.add_command(label="開く(O)...", command=open_file)
file_menu.add_command(label="保存(S)...", command=save_file)
file_menu.add_separator()  # 区切り線
file_menu.add_command(label="終了(X)", command=form.destroy)

# 「編集」メニューの作成
edit_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="編集(E)", menu=edit_menu)
edit_menu.add_command(label="切り取り(T)", command=cut_text)
edit_menu.add_command(label="コピー(C)", command=copy_text)
edit_menu.add_command(label="貼り付け(P)", command=paste_text)

# 「ヘルプ」メニューの作成
help_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="ヘルプ(H)", menu=help_menu)
help_menu.add_command(label="メモ帳風アプリについて(A)", command=show_about)


text_frame = tk.Frame(form)
text_frame.pack(expand=True, fill='both')

main_memo = tk.Text(text_frame, bg="white", fg="black", wrap=tk.WORD, font=("Helvetica", 12))
main_memo.pack(side='left', expand=True, fill='both')

scrollbar = tk.Scrollbar(text_frame, command=main_memo.yview)
scrollbar.pack(side='right', fill='y')
main_memo.config(yscrollcommand=scrollbar.set)

#画像挿入ボタンを作成
insert_button=tk.Button(form,text="画像を挿入",command=insert_image)
insert_button.pack(pady=10)

form.mainloop()#実行
import random
import tkinter as tk
from tkinter import Menu, scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk
import json
import os

image_refs = []  # 画像参照を保持するリスト
inserted_images = []



# --- 関数定義 ---
def new_file():
    """新規ファイルを作成"""
    main_memo.delete(1.0, tk.END)
    main_memo.title("ピクメモ")

def open_file():
    """ファイルを開く"""
    filepath = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )

    if not filepath:
        return
    
    try:
        # 既存の内容をクリア
        main_memo.delete(1.0, tk.END)
        inserted_images.clear()

        with open(filepath, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        
        # テキストを挿入
        main_memo.insert(tk.END, loaded_data.get("text_content", ""))

        # 画像を再挿入
        for img_path in loaded_data.get("images", []):
            if os.path.exists(img_path):
                original_image = Image.open(img_path)
                width = 300
                height = int(original_image.height * width / original_image.width)
                resized_image = original_image.resize((width, height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                
                main_memo.image_create(tk.END, image=photo)
                
                # 読み込んだ画像の参照とパスをリストに追加
                inserted_images.append({
                    "photo": photo,
                    "path": img_path
                })
            else:
                print(f"警告: 画像ファイルが見つかりません - {img_path}")

        messagebox.showinfo("読み込み完了", "ファイルが正常に読み込まれました。")

    except Exception as e:
        messagebox.showerror("エラー", f"ファイルの読み込み中にエラーが発生しました: {e}")


def save_file():
    """ファイルを保存"""
    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not filepath:
        return
    
    try:
        # テキストと画像のパスを辞書にまとめる
        data_to_save = {
            "text_content": main_memo.get(1.0, tk.END),
            "images": [img["path"] for img in inserted_images]
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)
        
        messagebox.showinfo("保存完了", "ファイルが正常に保存されました。")

    except Exception as e:
        messagebox.showerror("エラー", f"ファイルの保存中にエラーが発生しました: {e}")

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

        #画像の参照とパスをリストに保存
        inserted_images.append({
            "photo": photo,
            "path": filepath
        })

        image_refs.append(photo)  # 参照を保持してガーベジコレクションを防ぐ
    except Exception as e:
        messagebox.showerror("エラー", f"画像ファイルの読み込み中にエラーが発生しました: {e}")





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
import random
import tkinter as tk
from tkinter import Menu, scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk
import json
import os

inserted_images = {}

# --- 関数定義 ---
def new_file():
    """新規ファイルを作成"""
    main_memo.delete(1.0, tk.END)
    form.title("ピクメモ")

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
        # 画像参照をクリア
        inserted_images.clear()

        with open(filepath, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        

        # 読み込んだ要素を順に処理
        for item in loaded_data:
            if item["type"] == "text":
                main_memo.insert(tk.END, item["content"])
                print("1OK")
            elif item["type"] == "image":
                img_path = item["path"]
                if os.path.exists(img_path):
                    original_image = Image.open(img_path)
                    width = 300
                    height = int(original_image.height * width / original_image.width)
                    resized_image = original_image.resize((width, height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(resized_image)

                    # 画像を挿入し、画像名を取得
                    image_name = main_memo.image_create(tk.END, image=photo)
                    # 画像名をキーにしてパスとPhotoImageを保持
                    inserted_images[image_name] = {"photo": photo, "path": img_path}
                    print("2OK")
                else:
                    main_memo.insert(tk.END, f"[画像が見つかりません: {os.path.basename(img_path)}]")
                    print("3OK")

        print("読み込み完了", "ファイルが正常に読み込まれました。")
        form.title(os.path.basename(filepath))

    except Exception as e:
        print("エラー", f"ファイルの読み込み中にエラーが発生しました: {e}")

def save_file():
    """ファイルを保存"""
    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    if not filepath:
        return
    
    try:
        # ドキュメントの全内容（テキストと画像）を取得
        # Textウィジェットの全インデックスを取得
        data_to_save = []
        start_index = "1.0"
        end_index = main_memo.index(tk.END)

        # Text.dumpでテキストと画像の流れを取得
        dump = main_memo.dump(start_index, end_index, image=True, text=True)
        for i in range(len(dump)):
            tag = dump[i][0]
            if tag == "text":
                text = dump[i][1]
                if text:
                    data_to_save.append({"type": "text", "content": text})
            elif tag == "image":
                image_name = dump[i][1]
                image_info = inserted_images.get(image_name)
                if image_info and "path" in image_info:
                    data_to_save.append({"type": "image", "path": image_info["path"]})
                else:
                    messagebox.showwarning("警告", f"画像情報が見つかりません: {image_name}")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4)

        print("保存完了", "ファイルが正常に保存されました。")
        form.title(os.path.basename(filepath))

    except Exception as e:
        print("エラー", f"ファイルの保存中にエラーが発生しました: {e}")

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

        # 画像を挿入し、画像名を取得
        image_name = main_memo.image_create(tk.INSERT, image=photo)
        # 画像名をキーにしてパスとPhotoImageを保持
        inserted_images[image_name] = {"photo": photo, "path": filepath}

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
edit_menu.add_command(label="画像挿入(I)", command=insert_image)

# 「表示」メニューの作成
view_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="表示(V)", menu=view_menu)
view_menu.add_command(label="画面モード", command=lambda: messagebox.showinfo("画面モード", "画面モードの機能はまだ実装されていません。"))

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
#insert_button=tk.Button(form,text="画像を挿入",command=insert_image)
#insert_button.pack(pady=10)

form.mainloop()#実行
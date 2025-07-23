import random
import tkinter as tk
from tkinter import Menu, scrolledtext, filedialog, messagebox,ttk
from PIL import Image, ImageTk
import json
import os

inserted_images = {}
current_filepath = None  # 現在開いているファイルのパス
modified = False


# --- 関数定義 ---
def new_file():
    """新規ファイルを作成"""
    global current_filepath

    main_memo.delete(1.0, tk.END)
    form.title("ピクメモ")
    current_filepath = None  # 新規作成なのでパスはクリア

    modified = False  # 編集状態をリセット

def open_file():
    """ファイルを開く"""
    global current_filepath
    filepath = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )

    if not filepath:
        return
    
    current_filepath = filepath # ファイルパスを更新

    try:
        # 既存の内容をクリア
        main_memo.delete(1.0, tk.END)
        # 画像参照をクリア
        inserted_images.clear()

        with open(current_filepath, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
        

        # 読み込んだ要素を順に処理
        for item in loaded_data:
            if item["type"] == "text":# テキストの場合
                main_memo.insert(tk.END, item["content"])
            elif item["type"] == "image":# 画像の場合
                image_path = item["path"]# 画像のパスを取得
                if os.path.exists(image_path):# 画像ファイルが存在する場合
                    original_image = Image.open(image_path)# 画像を開く
                    
                    # 画像のサイズを300pxにリサイズ
                    width = 300
                    height = int(original_image.height * width / original_image.width)
                    resized_image = original_image.resize((width, height), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(resized_image)# 画像をPhotoImageに変換

                    # 画像を挿入し、画像名を取得
                    image_name = main_memo.image_create(tk.INSERT, image=photo)
                    # 画像名をキーにしてパスとPhotoImageを保持
                    inserted_images[image_name] = {"photo": photo, "path": image_path}


                    main_memo.tag_add(image_name, f"insert-1c") # image_nameをこのインデックスに追加
                    main_memo.tag_bind(image_name, "<Button-1>", lambda event, img_path=image_path: show_image_popup(img_path))
                    main_memo.tag_bind(image_name, "<Button-3>", lambda event, img_name=image_name: show_image_context_menu(event, img_name))
                    
                    main_memo.tag_bind(image_name, "<Enter>", lambda event: change_cursor_to_hand())
                    main_memo.tag_bind(image_name, "<Leave>", lambda event: restore_cursor())
                else:# 画像ファイルが存在しない場合
                    main_memo.insert(tk.END, f"[画像が見つかりません: {os.path.basename(image_path)}]")
        
        # 末尾の余計な改行を削除
        content = main_memo.get("1.0", tk.END)
        if content.endswith('\n'):
            main_memo.delete(f'end-2c', 'end')

        print("読み込み完了", "ファイルが正常に読み込まれました。")
        form.title(os.path.basename(filepath))
        modified = False  # 編集状態をリセット

    except Exception as e:
        print("エラー", f"ファイルの読み込み中にエラーが発生しました: {e}")

def save_file(overwrite=False):
    """ファイルを保存"""
    global current_filepath

    if overwrite and current_filepath:
        filepath = current_filepath
    else:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not filepath:
            return
        current_filepath = filepath
    
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
        modified = False  # 編集状態をリセット
        # Tkinterのmodifiedフラグもリセット
        main_memo.edit_modified(False)

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

def show_how_to_use():
    """使い方を表示"""
    messagebox.showinfo(
        "ショートカットキー",
        "各ボタンに書いてあるキーをCtrlキーと一緒に押すことで、\n"
        "同じ操作を行うことができます。"
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

        # 画像クリックイベントをバインド
        main_memo.tag_add(image_name, f"insert-1c")
        main_memo.tag_bind(image_name, "<Button-1>", lambda event, img_path=filepath: show_image_popup(img_path))
        main_memo.tag_bind(image_name, "<Button-3>", lambda event, img_name=image_name: show_image_context_menu(event, img_name))

        main_memo.tag_bind(image_name, "<Enter>", lambda event: change_cursor_to_hand())
        main_memo.tag_bind(image_name, "<Leave>", lambda event: restore_cursor())

    except Exception as e:
        messagebox.showerror("エラー", f"画像ファイルの読み込み中にエラーが発生しました: {e}")

def show_image_popup(img_path):
    try:
        popup = tk.Toplevel(form)
        popup.title("画像の拡大表示")
        img = Image.open(img_path)
        # 必要に応じて最大サイズを制限
        max_width, max_height = 800, 600
        w, h = img.size
        scale = min(max_width / w, max_height / h, 1.0)
        if scale < 1.0:
            img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(popup, image=photo)
        label.image = photo  # 参照保持
        label.pack()
    except Exception as e:
        messagebox.showerror("エラー", f"画像の拡大表示に失敗しました: {e}")

def put_one_back():
    """操作を1つ戻す"""
    try:
        main_memo.edit_undo()
    except tk.TclError:
        print("警告", "これ以上戻すことができません。")

def put_one_forward():
    """操作を1つ進める"""
    try:
        main_memo.edit_redo()
    except tk.TclError:
        print("警告", "これ以上進めることができません。")

def func_modified(event=None):
    """main_memoの編集状態が変更されたときに呼び出される関数"""
    global modified
    if main_memo.edit_modified():# 編集が行われた場合
        modified = True
    else:# 編集が行われていない場合
        modified = False

def on_closing():
    """アプリケーションを閉じる前に確認"""
    global modified
    if modified: # change_memoがTrueの場合
        result = messagebox.askyesnocancel("確認", "変更内容を保存しますか？")
        if result is None:  # キャンセルが選択された場合
            return
        elif result:  # はいが選択された場合
            save_file(overwrite=True)
    form.destroy()  # はいまたはいいえが選択された場合、アプリケーションを終了

def show_image_context_menu(event, image_name):
    context_menu = tk.Menu(form, tearoff=0)
    context_menu.add_command(label="画像の拡大表示", command=lambda: show_image_popup(inserted_images[image_name]['path']))
    context_menu.add_command(label="画像を削除", command=lambda: delete_image(image_name))
    context_menu.post(event.x_root, event.y_root)

def delete_image(image_name):
    # 画像が挿入されている位置を特定
    image_index = main_memo.image_cget(image_name, "image")
    # 画像を削除
    main_memo.delete(image_index)
    # inserted_images辞書からエントリを削除
    if image_name in inserted_images:
        del inserted_images[image_name]
    print(f"画像 '{image_name}' が削除されました。")

def change_cursor_to_hand():
    """カーソルを手の形に変更"""
    main_memo.config(cursor="hand2")

def restore_cursor():
    """カーソルをデフォルトに戻す"""
    main_memo.config(cursor="xterm") # または "arrow"


#---GUI---
form=tk.Tk()#tk作成
form.title("ピクメモ")
form.minsize(1000,560)
form.protocol("WM_DELETE_WINDOW", on_closing)

# メニューバーの作成
menubar=Menu(form)
form.config(menu=menubar)

# 「ファイル」メニューの作成
file_menu=Menu(menubar,tearoff=0)
menubar.add_cascade(label="ファイル",menu=file_menu)
file_menu.add_command(label="新規作成(N)", command=new_file)
file_menu.add_command(label="開く(O)", command=open_file)
file_menu.add_command(label="名前を付けて保存(S)", command=lambda: save_file(overwrite=False))
file_menu.add_command(label="上書き保存(S)", command=lambda: save_file(overwrite=True))
file_menu.add_separator()  # 区切り線
file_menu.add_command(label="終了(Q)", command=on_closing)

# 「編集」メニューの作成
edit_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="編集", menu=edit_menu)
edit_menu.add_command(label="切り取り(X)", command=cut_text)
edit_menu.add_command(label="コピー(C)", command=copy_text)
edit_menu.add_command(label="貼り付け(V)", command=paste_text)
edit_menu.add_command(label="画像挿入(I)", command=insert_image)
edit_menu.add_separator()  # 区切り線
edit_menu.add_command(label="一つ戻す(Z)", command=put_one_back)
edit_menu.add_command(label="一つ進める(Y)", command=put_one_forward)

# 「表示」メニューの作成
view_menu = Menu(menubar, tearoff=0)    
menubar.add_cascade(label="表示", menu=view_menu)
view_menu.add_command(label="画面モード", command=lambda: messagebox.showinfo("画面モード", "画面モードの機能はまだ実装されていません。"))

# 「ヘルプ」メニューの作成
help_menu = Menu(menubar, tearoff=0)
menubar.add_cascade(label="ヘルプ", menu=help_menu)
help_menu.add_command(label="メモ帳風アプリについて", command=show_about)
help_menu.add_command(label="ショートカットキー", command=show_how_to_use)

form.bind('<Control-n>', lambda event: new_file())
form.bind('<Control-o>', lambda event: open_file())
form.bind('<Control-s>', lambda event: save_file(overwrite=True))
form.bind('<Control-i>', lambda event: insert_image())
form.bind('<Control-z>', lambda event: put_one_back())
form.bind('<Control-y>', lambda event: put_one_forward())
form.bind('<Control-q>', lambda event: on_closing())

text_frame = tk.Frame(form)
text_frame.pack(expand=True, fill='both')

main_memo = tk.Text(text_frame, bg="white", fg="black", wrap=tk.WORD, font=("Consolas", 12), undo=True)
main_memo.pack(side='left', expand=True, fill='both')

scrollbar = tk.Scrollbar(text_frame, command=main_memo.yview)
scrollbar.pack(side='right', fill='y')
main_memo.config(yscrollcommand=scrollbar.set)

main_memo.bind('<<Modified>>', func_modified)

#画像挿入ボタンを作成
#insert_button=tk.Button(form,text="画像を挿入",command=insert_image)
#insert_button.pack(pady=10)

form.mainloop()#実行
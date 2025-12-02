
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from mysql.connector import Error
from decimal import Decimal

# ---------- Cấu hình kết nối MySQL (chỉnh lại cho phù hợp) ----------
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',   # <- đổi password
    'database': 'tv_store'
}
# --------------------------------------------------------------------

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        messagebox.showerror("Database Error", f"Không thể kết nối database:\n{e}")
        return None

# ---------- Database operations ----------
def create_tables_if_not_exist():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tv (
      id INT AUTO_INCREMENT PRIMARY KEY,
      model VARCHAR(100) NOT NULL,
      brand VARCHAR(100) NOT NULL,
      size_inch INT NOT NULL,
      price DECIMAL(12,2) NOT NULL,
      stock INT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales (
      id INT AUTO_INCREMENT PRIMARY KEY,
      tv_id INT NOT NULL,
      qty INT NOT NULL,
      total_price DECIMAL(12,2) NOT NULL,
      sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (tv_id) REFERENCES tv(id) ON DELETE RESTRICT
    ) ENGINE=InnoDB;
    """)
    conn.commit()
    cursor.close()
    conn.close()

def fetch_all_tvs(search_text=None):
    conn = get_connection()
    if not conn:
        return []
    cursor = conn.cursor(dictionary=True)
    if search_text:
        q = "%" + search_text + "%"
        cursor.execute("SELECT * FROM tv WHERE model LIKE %s OR brand LIKE %s ORDER BY id", (q, q))
    else:
        cursor.execute("SELECT * FROM tv ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def insert_tv(model, brand, size_inch, price, stock):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    sql = "INSERT INTO tv (model, brand, size_inch, price, stock) VALUES (%s,%s,%s,%s,%s)"
    cursor.execute(sql, (model, brand, size_inch, price, stock))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def update_tv(tv_id, model, brand, size_inch, price, stock):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    sql = "UPDATE tv SET model=%s, brand=%s, size_inch=%s, price=%s, stock=%s WHERE id=%s"
    cursor.execute(sql, (model, brand, size_inch, price, stock, tv_id))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def delete_tv(tv_id):
    conn = get_connection()
    if not conn: return False
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tv WHERE id=%s", (tv_id,))
        conn.commit()
    except Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e
    cursor.close()
    conn.close()
    return True

def create_sale(tv_id, qty):
    conn = get_connection()
    if not conn: return False, "DB fail"
    cursor = conn.cursor(dictionary=True)
    # check stock & price
    cursor.execute("SELECT id, price, stock, model FROM tv WHERE id=%s FOR UPDATE", (tv_id,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return False, "TV không tồn tại"
    if row['stock'] < qty:
        cursor.close()
        conn.close()
        return False, f"Tồn kho không đủ (còn {row['stock']})"
    total_price = Decimal(row['price']) * qty
    try:
        # insert sale
        cursor2 = conn.cursor()
        cursor2.execute("INSERT INTO sales (tv_id, qty, total_price) VALUES (%s,%s,%s)", (tv_id, qty, str(total_price)))
        # update stock
        cursor2.execute("UPDATE tv SET stock = stock - %s WHERE id=%s", (qty, tv_id))
        conn.commit()
        cursor2.close()
    except Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return False, str(e)
    cursor.close()
    conn.close()
    return True, f"Đã bán {qty} chiếc ({row['model']}), tổng {total_price} VND"

# ---------- GUI ----------
class TVStoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quản lý cửa hàng TIVI")
        self.geometry("900x520")
        # Frame trên: form nhập
        frm_top = ttk.Frame(self, padding=8)
        frm_top.pack(fill=tk.X)

        # Form fields
        ttk.Label(frm_top, text="Model:").grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)
        self.ent_model = ttk.Entry(frm_top, width=18)
        self.ent_model.grid(row=0, column=1, padx=4, pady=2)

        ttk.Label(frm_top, text="Brand:").grid(row=0, column=2, sticky=tk.W, padx=4, pady=2)
        self.ent_brand = ttk.Entry(frm_top, width=18)
        self.ent_brand.grid(row=0, column=3, padx=4, pady=2)

        ttk.Label(frm_top, text="Size (inch):").grid(row=0, column=4, sticky=tk.W, padx=4, pady=2)
        self.ent_size = ttk.Entry(frm_top, width=8)
        self.ent_size.grid(row=0, column=5, padx=4, pady=2)

        ttk.Label(frm_top, text="Price:").grid(row=1, column=0, sticky=tk.W, padx=4, pady=2)
        self.ent_price = ttk.Entry(frm_top, width=18)
        self.ent_price.grid(row=1, column=1, padx=4, pady=2)

        ttk.Label(frm_top, text="Stock:").grid(row=1, column=2, sticky=tk.W, padx=4, pady=2)
        self.ent_stock = ttk.Entry(frm_top, width=8)
        self.ent_stock.grid(row=1, column=3, padx=4, pady=2)

        # Buttons
        self.btn_add = ttk.Button(frm_top, text="Thêm", command=self.add_tv)
        self.btn_add.grid(row=1, column=4, padx=4)
        self.btn_update = ttk.Button(frm_top, text="Sửa", command=self.update_tv)
        self.btn_update.grid(row=1, column=5, padx=4)
        self.btn_delete = ttk.Button(frm_top, text="Xóa", command=self.delete_tv)
        self.btn_delete.grid(row=1, column=6, padx=4)

        # Search
        frm_search = ttk.Frame(self, padding=8)
        frm_search.pack(fill=tk.X)
        ttk.Label(frm_search, text="Tìm kiếm (model/brand):").pack(side=tk.LEFT)
        self.ent_search = ttk.Entry(frm_search, width=30)
        self.ent_search.pack(side=tk.LEFT, padx=6)
        ttk.Button(frm_search, text="Tìm", command=self.search_tv).pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_search, text="Làm mới", command=self.load_tvs).pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_search, text="Bán hàng", command=self.sell_dialog).pack(side=tk.RIGHT, padx=4)

        # Treeview list
        cols = ("id","model","brand","size","price","stock","created_at")
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            # set widths
            if c == "id": self.tree.column(c, width=40, anchor=tk.CENTER)
            elif c == "model": self.tree.column(c, width=140)
            elif c == "brand": self.tree.column(c, width=100)
            elif c == "size": self.tree.column(c, width=60, anchor=tk.CENTER)
            elif c == "price": self.tree.column(c, width=110, anchor=tk.E)
            elif c == "stock": self.tree.column(c, width=60, anchor=tk.CENTER)
            else: self.tree.column(c, width=160)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # status bar
        self.status = ttk.Label(self, text="Sẵn sàng", relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

        # load
        create_tables_if_not_exist()
        self.load_tvs()

    def set_status(self, txt):
        self.status.config(text=txt)

    def clear_form(self):
        self.ent_model.delete(0, tk.END)
        self.ent_brand.delete(0, tk.END)
        self.ent_size.delete(0, tk.END)
        self.ent_price.delete(0, tk.END)
        self.ent_stock.delete(0, tk.END)

    def load_tvs(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = fetch_all_tvs()
        for r in rows:
            self.tree.insert('', tk.END, values=(r['id'], r['model'], r['brand'], r['size_inch'], f"{r['price']}", r['stock'], r['created_at']))
        self.set_status(f"Đã tải {len(rows)} tivi")

    def search_tv(self):
        q = self.ent_search.get().strip()
        for row in self.tree.get_children():
            self.tree.delete(row)
        rows = fetch_all_tvs(search_text=q if q else None)
        for r in rows:
            self.tree.insert('', tk.END, values=(r['id'], r['model'], r['brand'], r['size_inch'], f"{r['price']}", r['stock'], r['created_at']))
        self.set_status(f"Kết quả: {len(rows)}")

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        vals = self.tree.item(selected[0])['values']
        # id, model, brand, size, price, stock, created_at
        self.selected_id = vals[0]
        self.ent_model.delete(0, tk.END); self.ent_model.insert(0, vals[1])
        self.ent_brand.delete(0, tk.END); self.ent_brand.insert(0, vals[2])
        self.ent_size.delete(0, tk.END); self.ent_size.insert(0, vals[3])
        self.ent_price.delete(0, tk.END); self.ent_price.insert(0, vals[4])
        self.ent_stock.delete(0, tk.END); self.ent_stock.insert(0, vals[5])

    def add_tv(self):
        try:
            model = self.ent_model.get().strip()
            brand = self.ent_brand.get().strip()
            size = int(self.ent_size.get().strip())
            price = Decimal(self.ent_price.get().strip())
            stock = int(self.ent_stock.get().strip())
            if not model or not brand:
                raise ValueError("Model và brand không được để trống")
        except Exception as e:
            messagebox.showwarning("Dữ liệu không hợp lệ", str(e))
            return
        ok = insert_tv(model, brand, size, str(price), stock)
        if ok:
            self.load_tvs()
            self.clear_form()
            self.set_status("Đã thêm tivi")
        else:
            messagebox.showerror("Lỗi", "Không thể thêm tivi")

    def update_tv(self):
        if not hasattr(self, 'selected_id'):
            messagebox.showinfo("Chọn tivi", "Vui lòng chọn tivi cần sửa trong danh sách")
            return
        try:
            tv_id = int(self.selected_id)
            model = self.ent_model.get().strip()
            brand = self.ent_brand.get().strip()
            size = int(self.ent_size.get().strip())
            price = Decimal(self.ent_price.get().strip())
            stock = int(self.ent_stock.get().strip())
            if not model or not brand:
                raise ValueError("Model và brand không được để trống")
        except Exception as e:
            messagebox.showwarning("Dữ liệu không hợp lệ", str(e))
            return
        ok = update_tv(tv_id, model, brand, size, str(price), stock)
        if ok:
            self.load_tvs()
            self.set_status("Đã cập nhật")
        else:
            messagebox.showerror("Lỗi", "Cập nhật thất bại")

    def delete_tv(self):
        if not hasattr(self, 'selected_id'):
            messagebox.showinfo("Chọn tivi", "Vui lòng chọn tivi cần xóa")
            return
        tv_id = int(self.selected_id)
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa tivi đã chọn?"):
            try:
                delete_tv(tv_id)
                self.load_tvs()
                self.clear_form()
                self.set_status("Đã xóa")
            except Error as e:
                messagebox.showerror("Lỗi", f"Không thể xóa: {e}")

    def sell_dialog(self):
        # lấy selected
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Chọn tivi", "Vui lòng chọn tivi để bán")
            return
        vals = self.tree.item(selected[0])['values']
        tv_id = vals[0]
        model = vals[1]
        stock = int(vals[5])
        q = simpledialog.askinteger("Bán hàng", f"Bán bao nhiêu chiếc của {model}? (tồn {stock})", minvalue=1, maxvalue=stock)
        if q is None:
            return
        success, msg = create_sale(tv_id, q)
        if success:
            messagebox.showinfo("Thành công", msg)
            self.load_tvs()
            self.set_status("Giao dịch bán hàng hoàn tất")
        else:
            messagebox.showerror("Thất bại", msg)

if __name__ == "__main__":
    app = TVStoreApp()
    app.mainloop()

-- 1. T?o database
CREATE DATABASE tv_store;
GO

USE tv_store;
GO

-- 2. T?o b?ng s?n ph?m (tivi)
CREATE TABLE tv (
    id INT IDENTITY(1,1) PRIMARY KEY, -- Trong SQL Server dùng IDENTITY thay cho AUTO_INCREMENT
    model NVARCHAR(100) NOT NULL,     -- Dùng NVARCHAR ?? h? tr? ti?ng Vi?t
    brand NVARCHAR(100) NOT NULL,
    size_inch INT NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    stock INT NOT NULL,
    created_at DATETIME DEFAULT GETDATE() -- Dùng GETDATE() thay cho CURRENT_TIMESTAMP
);
GO

-- 3. T?o b?ng bán hàng (sales)
CREATE TABLE sales (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tv_id INT NOT NULL,
    qty INT NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    sale_date DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (tv_id) REFERENCES tv(id) -- Khóa ngo?i
);
GO

-- 4. Thêm d? li?u m?u (nh? dòng cu?i trong ?nh c?a b?n)
INSERT INTO tv (model, brand, size_inch, price, stock)
VALUES ('X123', 'Samsung', 40, 8990000, 10);
GO
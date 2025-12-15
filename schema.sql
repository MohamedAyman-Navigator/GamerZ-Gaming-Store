-- Create Database (if not exists)
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'Gamerz__db')
BEGIN
    CREATE DATABASE Gamerz__db;
END
GO

USE Gamerz__db;
GO

-- Users Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[users](
        [id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [username] [nvarchar](50) NOT NULL UNIQUE,
        [password] [nvarchar](255) NOT NULL,
        [email] [nvarchar](100) NULL,
        [profile_photo] [nvarchar](255) NULL
    );
END
GO

-- Games Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[games]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[games](
        [id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [title] [nvarchar](255) NOT NULL,
        [price] [decimal](10, 2) NULL,
        [original_price] [decimal](10, 2) NULL,
        [image] [nvarchar](500) NULL,
        [trailer] [nvarchar](500) NULL,
        [description] [nvarchar](max) NULL,
        [genre] [nvarchar](255) NULL,
        [rating] [decimal](3, 1) NULL,
        [stock_quantity] [int] DEFAULT 0,
        [section] [nvarchar](50) NULL,
        [release_date] [nvarchar](50) NULL
    );
END
GO

-- Orders Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[orders]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[orders](
        [id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [user_id] [int] NOT NULL,
        [game_id] [int] NOT NULL,
        [key] [nvarchar](100) NOT NULL,
        [purchase_date] [datetime] DEFAULT GETDATE(),
        FOREIGN KEY([user_id]) REFERENCES [dbo].[users] ([id]),
        FOREIGN KEY([game_id]) REFERENCES [dbo].[games] ([id])
    );
END
GO

-- Game Specs Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[game_specs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[game_specs](
        [id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [game_id] [int] NOT NULL,
        [min_os] [nvarchar](255) NULL,
        [min_cpu] [nvarchar](255) NULL,
        [min_ram] [nvarchar](255) NULL,
        [min_gpu] [nvarchar](255) NULL,
        [min_storage] [nvarchar](255) NULL,
        [rec_os] [nvarchar](255) NULL,
        [rec_cpu] [nvarchar](255) NULL,
        [rec_ram] [nvarchar](255) NULL,
        [rec_gpu] [nvarchar](255) NULL,
        [rec_storage] [nvarchar](255) NULL,
        FOREIGN KEY([game_id]) REFERENCES [dbo].[games] ([id]) ON DELETE CASCADE
    );
END
GO

-- Game DLCs Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[game_dlcs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[game_dlcs](
        [id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [game_id] [int] NOT NULL,
        [title] [nvarchar](255) NOT NULL,
        [price] [decimal](10, 2) NULL,
        [original_price] [decimal](10, 2) NULL,
        [description] [nvarchar](max) NULL,
        [image] [nvarchar](500) NULL,
        FOREIGN KEY([game_id]) REFERENCES [dbo].[games] ([id]) ON DELETE CASCADE
    );
END
GO

-- Game Editions Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[game_editions]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[game_editions](
        [id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [game_id] [int] NOT NULL,
        [title] [nvarchar](255) NOT NULL,
        [price] [decimal](10, 2) NULL,
        [original_price] [decimal](10, 2) NULL,
        [description] [nvarchar](max) NULL,
        [image] [nvarchar](500) NULL,
        FOREIGN KEY([game_id]) REFERENCES [dbo].[games] ([id]) ON DELETE CASCADE
    );
END
GO

-- Game Screenshots Table
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[game_screenshots]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[game_screenshots](
        [id] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
        [game_id] [int] NOT NULL,
        [image_url] [nvarchar](500) NOT NULL,
        FOREIGN KEY([game_id]) REFERENCES [dbo].[games] ([id]) ON DELETE CASCADE
    );
END
GO

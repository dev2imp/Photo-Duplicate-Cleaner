# Photo Duplicate Cleaner

A Python + Docker tool for organizing large photo collections by detecting **exact duplicates and visually similar images**, separating videos, identifying unreadable images, and generating a detailed HTML report.

The tool scans the selected folder recursively, including all subfolders.

Instead of automatically deleting duplicate files, it creates a separate result directory where unique images, duplicate groups, videos, unreadable files, and the analysis report are organized.

---

## ✨ Features

* 🔍 Recursively scans folders and subfolders
* 🖼️ Detects image files
* 🎥 Detects and separates video files
* 🧩 Finds exact duplicate images
* 🧠 Finds visually similar images
* 📐 Handles images with different resolutions and sizes
* 📱 Can detect compressed copies, such as WhatsApp images
* 🔄 Can detect rotated or modified versions of an image
* 🏆 Keeps the highest-resolution / largest image from each duplicate group
* 📦 Organizes duplicates into separate groups
* ⚠️ Separates unreadable or corrupted images
* 📊 Generates a detailed HTML report
* 🧪 Supports a safe `dry` / test mode
* 📋 Supports `copy` and `move` modes
* 🐳 Runs inside Docker
* 🪟 Easy Windows startup using `run.bat`
* 🔒 Duplicate files are never automatically deleted

---

# How It Works

The application recursively scans the folder you provide.

For example:

```text
C:\Photos
```

The folder may contain:

```text
C:\Photos
├── Holiday
│   ├── beach.jpg
│   ├── beach_copy.jpg
│   └── holiday.mp4
│
├── WhatsApp
│   ├── IMG001.jpg
│   └── IMG002.jpg
│
└── Phone
    ├── beach.jpg
    └── family.png
```

The application analyzes the files and separates them into different categories.

```text
                    Source Folder
                         │
                         ▼
                  Recursive Scan
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Images          Videos         Other Files
          │              │              │
          ▼              ▼              │
 Duplicate /         Videos            Ignored
 Similarity          Folder
 Analysis
          │
     ┌────┴────┐
     ▼         ▼
  Unique    Duplicates
  Images     Groups
```

---

# Image Duplicate Detection

The application can identify both **exact duplicates** and **visually similar images**.

## Exact Duplicates

Files that contain the same image can be identified even if they have different filenames.

For example:

```text
photo.jpg
photo_copy.jpg
backup_photo.jpg
```

If they represent the same image, they can be placed in the same duplicate group.

---

## Visually Similar Images

Images do not necessarily have to be binary-identical to be considered similar.

The tool can detect cases such as:

* Different image resolutions
* Resized images
* Compressed images
* WhatsApp-compressed copies
* Re-saved images
* Rotated versions
* Visually similar copies

For example:

```text
original.jpg
whatsapp_image.jpg
original_resized.jpg
original_rotated.jpg
```

may be recognized as belonging to the same similarity group depending on the configured threshold.

---

# 🏆 Choosing the Best Image

When multiple similar images are found, the application selects the **highest-resolution / largest file** as the main image for that group.

For example:

```text
Duplicate Group

photo_original.jpg       4000 × 3000
photo_whatsapp.jpg       1280 × 960
photo_copy.jpg           1920 × 1440
```

The application keeps:

```text
photo_original.jpg
```

as the main image because it has the highest resolution.

The remaining files are placed in the corresponding duplicate group.

---

# 📂 Output Structure

If the input folder is:

```text
C:\Photos
```

the application creates:

```text
C:\Photos_sonuc
```

The result directory has the following structure:

```text
C:\Photos_sonuc
│
├── UniqueImages
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── photo3.png
│
├── Duplicates
│   ├── group_0001
│   │   ├── photo1_copy.jpg
│   │   └── photo1_whatsapp.jpg
│   │
│   ├── group_0002
│   │   ├── beach_copy.jpg
│   │   └── beach_resized.jpg
│   │
│   └── ...
│
├── Videos
│   ├── holiday.mp4
│   ├── birthday.mov
│   └── family_video.mp4
│
├── Unreadable
│   ├── corrupted.jpg
│   └── broken.png
│
└── report.html
```

---

# 📁 UniqueImages

The `UniqueImages/` directory contains:

1. Images that were not identified as duplicates.
2. The best-quality image selected from each duplicate/similarity group.

For example:

```text
UniqueImages/
├── family.jpg
├── holiday.jpg
├── beach.png
└── birthday.jpg
```

If a group contains multiple copies of the same image, the highest-resolution / largest image from that group is kept here.

---

# 📦 Duplicates

Duplicate files are **not deleted**.

Instead, they are organized into individual groups:

```text
Duplicates/
├── group_0001
│   ├── holiday_copy.jpg
│   └── holiday_whatsapp.jpg
│
├── group_0002
│   ├── beach_1.jpg
│   └── beach_compressed.jpg
│
└── group_0003
    └── family_backup.jpg
```

Each group corresponds to a main image located inside `UniqueImages/`.

This makes it easy to understand which files were considered duplicates of each other.

---

# 🎥 Videos

Video files are detected and separated from images.

They are moved/copied to:

```text
Videos/
```

For example:

```text
Videos/
├── holiday.mp4
├── birthday.mov
└── family_video.mp4
```

### Important

Videos are **not analyzed for visual similarity**.

The tool only identifies and separates them.

---

# ⚠️ Unreadable Images

Images that cannot be opened or processed correctly are placed into:

```text
Unreadable/
```

For example:

```text
Unreadable/
├── corrupted.jpg
└── broken.png
```

These files are not included in the normal duplicate analysis.

This makes it easier to identify potentially corrupted images in a large archive.

---

# 📊 HTML Report

After processing, the application generates:

```text
report.html
```

The report provides a visual overview of the detected duplicate groups.

For example:

```text
Original
└── photo.jpg

Duplicates
├── photo_copy.jpg
├── photo_whatsapp.jpg
└── photo_resized.jpg
```

The report helps you understand:

* Which files were considered similar
* Which image was selected as the main/original image
* Which files were classified as duplicates
* Which duplicate group each file belongs to
* Where the files were placed in the output directory

This is especially useful when processing thousands of images because you can review the results without manually searching through every folder.

---

# 🪟 Windows Usage

## Requirements

Before running the application, make sure you have:

* Windows
* Docker Desktop
* Docker Desktop running

---

## Run with `run.bat`

The easiest way to start the application is to double-click:

```text
run.bat
```

You can also run it from Command Prompt:

```cmd
run.bat
```

Or provide the image directory directly:

```cmd
run.bat C:\Photos
```

The application will then use the provided folder as its input directory.

---

# 🧪 Test Mode

The first time you run the application, it is strongly recommended to use:

```text
MODE=dry
```

The `dry` mode performs the analysis without modifying, moving, or copying your files.

It allows you to:

1. Scan the image collection
2. Detect duplicate groups
3. Generate the HTML report
4. Review the results
5. Adjust the similarity threshold if necessary

No files are changed during the analysis.

This makes `dry` mode the safest way to test the application on a new photo collection.

---

# ⚙️ Operation Modes

The application supports three modes.

## `dry`

Test mode.

```text
MODE=dry
```

The application analyzes the files and generates the results without moving or copying anything.

**Recommended for the first run.**

---

## `copy`

```text
MODE=copy
```

Files are copied to the appropriate output directories.

The original files remain in their original locations.

This is useful when you want to keep the original folder completely untouched.

---

## `move`

```text
MODE=move
```

Files are moved to their appropriate output directories.

Before using `move`, it is strongly recommended to run the application in `dry` mode first and review `report.html`.

---

# 🎚️ Similarity Threshold

The similarity sensitivity can be configured using:

```text
THRESHOLD
```

The default value is:

```text
THRESHOLD=8
```

The supported range is:

```text
0 - 256
```

In general:

```text
Lower threshold
       ↓
Stricter similarity detection
       ↓
Fewer images considered similar
```

While:

```text
Higher threshold
       ↓
More tolerant similarity detection
       ↓
More images considered similar
```

### Recommended Values

If burst/series photos are very similar and too many are being grouped together, try:

```text
THRESHOLD=4
```

or:

```text
THRESHOLD=6
```

If some obvious duplicates are not being detected, try:

```text
THRESHOLD=10
```

or:

```text
THRESHOLD=12
```

It is recommended to test different values using `MODE=dry` before running the application in `copy` or `move` mode.

---

# 🐳 Docker

The application runs inside Docker, so the required Python environment is isolated from the host system.

## Build the Docker Image

```bash
docker build -t foto-duplicate .
```

## Run the Container Manually

Example:

```bash
docker run --rm \
  -v "C:\Photos":/data/input \
  -v "C:\Photos_sonuc":/data/output \
  -e MODE=dry \
  foto-duplicate
```

The input directory is:

```text
C:\Photos
```

and the output directory is:

```text
C:\Photos_sonuc
```

---

# 🔄 Processing Workflow

The complete processing flow is:

```text
                 Input Folder
                      │
                      ▼
               Recursive Scan
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
       Images       Videos     Other Files
          │           │           │
          ▼           ▼           │
   Similarity       Videos         │
     Analysis       Folder         │
          │                       │
     ┌────┴────┐                  │
     ▼         ▼                  │
  Unique    Duplicates            │
  Images      Groups              │
     │         │                  │
     └────┬────┘                  │
          │                       │
          └──────────┬────────────┘
                     ▼
                HTML Report
```

---

# 🔒 File Safety

The application is designed to avoid automatically deleting duplicate files.

Instead, it creates a separate output directory:

```text
C:\Photos
```

becomes:

```text
C:\Photos_sonuc
```

This allows you to inspect the results before making any permanent changes to your original collection.

### Important

Duplicate files are **never automatically deleted by the application**.

They are preserved inside:

```text
Duplicates/
```

so you can manually review them.

---

# 📌 Important Notes

## Large Archives

Large photo collections may take several minutes to process.

For example, archives containing:

```text
20,000+
```

images may require more processing time because images need to be compared.

Processing time depends on:

* Number of images
* Image sizes
* Number of duplicate groups
* CPU performance
* Storage speed

---

## Videos

Videos are only separated:

```text
Video → Videos/
```

No video similarity or duplicate analysis is performed.

---

## Other Files

Files that are not images or videos are ignored.

For example:

```text
.txt
.pdf
.docx
.xlsx
.zip
.exe
```

These files are not moved, copied, analyzed, or deleted by the image-processing workflow.

---

# 💡 Recommended Workflow

For a new photo archive, the recommended workflow is:

### 1. Start with Test Mode

```text
MODE=dry
```

### 2. Use the Default Threshold

Start with:

```text
THRESHOLD=8
```

### 3. Review `report.html`

Check whether the detected groups make sense.

### 4. Inspect the Output

Review:

```text
UniqueImages/
Duplicates/
Videos/
Unreadable/
```

### 5. Adjust the Threshold if Necessary

If too many similar images are grouped together, lower the threshold.

If duplicates are being missed, increase it.

### 6. Run in `copy` or `move` Mode

Once you are satisfied with the results, choose:

```text
MODE=copy
```

or:

```text
MODE=move
```

---

# 📋 Feature Overview

| Feature                         | Supported |
| ------------------------------- | --------- |
| Recursive folder scanning       | ✅         |
| Exact duplicate detection       | ✅         |
| Visual similarity detection     | ✅         |
| Different image resolutions     | ✅         |
| Compressed image detection      | ✅         |
| WhatsApp copies                 | ✅         |
| Rotated images                  | ✅         |
| Highest-quality image selection | ✅         |
| Duplicate grouping              | ✅         |
| Duplicate deletion              | ❌         |
| Video separation                | ✅         |
| Video similarity analysis       | ❌         |
| Unreadable image detection      | ✅         |
| HTML report                     | ✅         |
| Dry/Test mode                   | ✅         |
| Copy mode                       | ✅         |
| Move mode                       | ✅         |
| Configurable threshold          | ✅         |
| Docker                          | ✅         |
| Windows `run.bat`               | ✅         |

---

# 🚀 Quick Start

The simplest workflow is:

```text
1. Start Docker Desktop
        ↓
2. Run run.bat
        ↓
3. Provide your photo folder
        ↓
4. Start with MODE=dry
        ↓
5. Review report.html
        ↓
6. Check UniqueImages and Duplicates
        ↓
7. Adjust THRESHOLD if necessary
        ↓
8. Run with copy or move mode
```

---

# License

Add your preferred license here.

Example:

```text
MIT License
```

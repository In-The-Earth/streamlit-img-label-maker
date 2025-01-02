import streamlit as st
import os
from PIL import Image
from streamlit_img_label import st_img_label
from streamlit_img_label.manage import ImageManager, ImageDirManager


def get_save_directory():
    """ให้ผู้ใช้ระบุโฟลเดอร์สำหรับบันทึกไฟล์"""
    save_dir = st.sidebar.text_input("Save Directory", value="img_dir", help="Enter the directory to save files.")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    return save_dir

def upload_class_file():
    """ฟังก์ชันสำหรับอัปโหลดและอ่าน labels จาก class.txt"""
    # ตั้งชื่อไฟล์ที่จะเก็บ labels
    class_file_path = os.path.join("img_dir", "class.txt")

    # ถ้ามีการอัปโหลด class.txt ใหม่
    uploaded_file = st.sidebar.file_uploader(
        "Upload class.txt", type=["txt"], help="Upload a text file with one label per line."
    )

    if uploaded_file is not None:
        # อ่าน labels จากไฟล์ที่อัปโหลด
        labels = [line.strip() for line in uploaded_file.read().decode("utf-8").splitlines()]
        st.session_state["labels"] = labels
        
        # เก็บ class.txt ลงในไฟล์
        with open(class_file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(labels))
        
        # เริ่มต้น 'used_labels' หากยังไม่มีใน session_state
        if "used_labels" not in st.session_state:
            st.session_state["used_labels"] = []

        st.success("Labels updated successfully!")
    else:
        # ถ้ามี class.txt อยู่แล้วให้ใช้จากไฟล์ที่เก็บไว้
        if os.path.exists(class_file_path):
            with open(class_file_path, "r", encoding="utf-8") as f:
                labels = [line.strip() for line in f.readlines()]
            st.session_state["labels"] = labels
        else:
            # ถ้ายังไม่มี class.txt ให้แสดงข้อความแจ้งเตือน
            st.error("Please upload class.txt before continuing.")
            labels = []  # กำหนดให้ labels เป็นค่าว่างหากยังไม่มีการอัปโหลด

    return labels


def save_yolo_format(im, rects, labels, save_dir, img_file_name):
    """บันทึก Annotation ในรูปแบบ YOLO"""
    img_width, img_height = im.get_img().size  # ขนาดของภาพ
    yolo_annotations = []

    for rect in rects:
        # Use the correct keys from the dictionary
        x_min, y_min = rect["left"], rect["top"]
        x_max, y_max = rect["left"] + rect["width"], rect["top"] + rect["height"]
        class_name = rect["label"]

        if class_name not in labels:
            continue

        class_index = labels.index(class_name)
        x_center = (x_min + x_max) / 2 / img_width
        y_center = (y_min + y_max) / 2 / img_height
        width = (x_max - x_min) / img_width
        height = (y_max - y_min) / img_height

        yolo_annotations.append(f"{class_index} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    # Save YOLO annotations to .txt file
    txt_file_name = os.path.join(save_dir, img_file_name.split(".")[0] + ".txt")
    with open(txt_file_name, "w") as f:
        f.write("\n".join(yolo_annotations))

def show_label_count():
    # ตรวจสอบว่า label count มีข้อมูลหรือไม่
    if "label_count" in st.session_state:
        with st.expander("Label Count", expanded=False):  # เปิดเป็นค่าเริ่มต้นที่ปิด
            for label, count in st.session_state["label_count"].items():
                st.write(f"{label}: {count}")

def upload_images(save_dir):
    """ฟังก์ชันสำหรับการอัปโหลดหลายรูปภาพและบันทึกลงในโฟลเดอร์"""
    uploaded_images = st.sidebar.file_uploader(
        "Upload Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True, help="Upload multiple image files."
    )

    if uploaded_images:
        img_list = []
        for uploaded_image in uploaded_images:
            # อ่านและแสดงภาพ
            img = Image.open(uploaded_image)
            # st.image(img, caption="Uploaded Image", use_column_width=True)

            # บันทึกรูปภาพลงในโฟลเดอร์ที่กำหนด
            img_save_path = os.path.join(save_dir, uploaded_image.name)
            img.save(img_save_path)
            img_list.append(uploaded_image.name)  # เก็บชื่อไฟล์ที่บันทึก

        # อัปเดต st.session_state["files"]
        if "files" not in st.session_state:
            st.session_state["files"] = []
        
        # เพิ่มไฟล์ที่อัปโหลดเข้าไปใน files
        st.session_state["files"].extend(img_list)

        st.success("Images saved and files updated successfully!")
        return img_list
    else:
        return []

def run():
    labels = upload_class_file()
    default_dir = "img_dir"
    save_dir = get_save_directory()
    idm = ImageDirManager(save_dir)

    # อัปโหลดรูปภาพ
    uploaded_images = upload_images(default_dir)  # อัปโหลดและบันทึกรูป

    # if uploaded_images:
    #     st.write("Images uploaded and saved successfully!")
    #     for img_path in uploaded_images:
    #         st.write(f"Image saved at: {img_path}")

    # Sidebar: เลือกรูปแบบการบันทึก
    global save_format
    save_format = st.sidebar.radio(
        "Select save format",
        options=["VOC (XML)", "YOLO"],
        help="Choose the format to save annotations.",
        index=1  # Set default index to 1 (which corresponds to "YOLO")
    )

    if "files" not in st.session_state:
        st.session_state["files"] = idm.get_all_files()
        st.session_state["annotation_files"] = idm.get_exist_annotation_files()
        st.session_state["image_index"] = 0
        st.session_state["used_labels"] = []  # เก็บ label ที่ใช้
        st.session_state["label_count"] = {label: 0 for label in labels}  # สร้าง dictionary สำหรับนับจำนวนแต่ละ label
    else:
        idm.set_all_files(st.session_state["files"])
        idm.set_annotation_files(st.session_state["annotation_files"])

    def refresh():
        st.session_state["files"] = idm.get_all_files()
        st.session_state["annotation_files"] = idm.get_exist_annotation_files()
        st.session_state["image_index"] = 0

    def next_image():
        image_index = st.session_state["image_index"]
        if image_index < len(st.session_state["files"]) - 1:
            st.session_state["image_index"] += 1
        else:
            st.warning('This is the last image.')

    def previous_image():
        image_index = st.session_state["image_index"]
        if image_index > 0:
            st.session_state["image_index"] -= 1
        else:
            st.warning('This is the first image.')

    def next_annotate_file():
        image_index = st.session_state["image_index"]
        next_image_index = idm.get_next_annotation_image(image_index)
        if next_image_index:
            st.session_state["image_index"] = idm.get_next_annotation_image(image_index)
        else:
            st.warning("All images are annotated.")
            next_image()

    def go_to_image():
        file_index = st.session_state["files"].index(st.session_state["file"])
        st.session_state["image_index"] = file_index

    # Sidebar: show status
    n_files = len(st.session_state["files"])
    n_annotate_files = len(st.session_state["annotation_files"])
    st.sidebar.write("Total files:", n_files)
    st.sidebar.write("Total annotate files:", n_annotate_files)
    st.sidebar.write("Remaining files:", n_files - n_annotate_files)

    # แสดง label ที่ใช้แล้ว
    st.sidebar.write("Used Labels:", st.session_state.get("used_labels", []))

    # # แสดงจำนวน label ที่ใช้แล้ว
    # st.sidebar.write("Label Count:")
    # for label, count in st.session_state["label_count"].items():
    #     st.sidebar.write(f"{label}: {count}")
    show_label_count()
    st.sidebar.selectbox(
        "Files",
        st.session_state["files"],
        index=st.session_state["image_index"],
        on_change=go_to_image,
        key="file",
    )
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.button(label="Previous image", on_click=previous_image)
    with col2:
        st.button(label="Next image", on_click=next_image)
    st.sidebar.button(label="Next need annotate", on_click=next_annotate_file)
    st.sidebar.button(label="Refresh", on_click=refresh)

    # Main content: annotate images
    img_file_name = idm.get_image(st.session_state["image_index"])
    img_path = os.path.join(default_dir, img_file_name)
    im = ImageManager(img_path)
    img = im.get_img()
    resized_img = im.resizing_img()
    resized_rects = im.get_resized_rects()
    rects = st_img_label(resized_img, box_color="red", rects=resized_rects)

    def annotate():
        if save_format == "VOC (XML)":
            im.save_annotation()  # บันทึกแบบ VOC
            annotation_file_name = img_file_name.split(".")[0] + ".xml"
        elif save_format == "YOLO":
            save_yolo_format(im, rects, labels, save_dir, img_file_name)  # บันทึกแบบ YOLO
            annotation_file_name = img_file_name.split(".")[0] + ".txt"

            # บันทึก label ที่ถูกใช้ไปแล้วและนับจำนวน
            for rect in rects:
                class_name = rect.get("label", "")
                if class_name:
                    # ตรวจสอบว่า class_name อยู่ใน label_count แล้วหรือยัง
                    if class_name not in st.session_state["label_count"]:
                        st.session_state["label_count"][class_name] = 0  # ถ้ายังไม่มีให้เพิ่มค่าเริ่มต้นเป็น 0
                    if class_name not in st.session_state["used_labels"]:
                        st.session_state["used_labels"].append(class_name)
                    st.session_state["label_count"][class_name] += 1

        if annotation_file_name not in st.session_state["annotation_files"]:
            st.session_state["annotation_files"].append(annotation_file_name)
        next_annotate_file()

    if rects:
        st.button(label="Save", on_click=annotate)
        preview_imgs = im.init_annotation(rects)

        for i, prev_img in enumerate(preview_imgs):
            prev_img[0].thumbnail((200, 200))
            col1, col2 = st.columns(2)
            with col1:
                col1.image(prev_img[0])
            with col2:
                default_index = 0
                if prev_img[1]:
                    default_index = labels.index(prev_img[1])

                select_label = col2.selectbox(
                    "Label", labels, key=f"label_{i}", index=default_index
                )
                im.set_annotation(i, select_label)


if __name__ == "__main__":
    run()

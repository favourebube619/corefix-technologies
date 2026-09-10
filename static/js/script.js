/* =====================================================
   COREFIX TECHNOLOGIES
   MAIN WEBSITE JAVASCRIPT
   FLASK + SQLITE VERSION
===================================================== */


/* =====================================================
   BOOK REPAIR ELEMENTS
===================================================== */

const repairForm =
    document.getElementById("repairForm");

const successMessage =
    document.getElementById("successMessage");

const generatedRepairId =
    document.getElementById("generatedRepairId");

const copyRepairId =
    document.getElementById("copyRepairId");

const newRepairBtn =
    document.getElementById("newRepairBtn");


/* =====================================================
   SUBMIT REPAIR REQUEST
===================================================== */

if (repairForm) {

    repairForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();
            event.stopPropagation();


            const submitButton =
                repairForm.querySelector(
                    ".booking-btn"
                );


            if (!submitButton) {
                return;
            }


            const originalButtonText =
                submitButton.textContent;


            submitButton.disabled =
                true;


            submitButton.textContent =
                "Submitting...";


            const nameInput =
                document.getElementById("name");

            const phoneInput =
                document.getElementById("phone");

            const deviceInput =
                document.getElementById("device");

            const brandInput =
                document.getElementById("brand");

            const modelInput =
                document.getElementById("model");

            const issueInput =
                document.getElementById("issue");

            const descriptionInput =
                document.getElementById(
                    "description"
                );

            const contactMethodInput =
                document.getElementById(
                    "contact-method"
                );


            const repairRequest = {

                name:
                    nameInput
                        ? nameInput.value.trim()
                        : "",

                phone:
                    phoneInput
                        ? phoneInput.value.trim()
                        : "",

                device:
                    deviceInput
                        ? deviceInput.value
                        : "",

                brand:
                    brandInput
                        ? brandInput.value
                        : "",

                model:
                    modelInput
                        ? modelInput.value.trim()
                        : "",

                issue:
                    issueInput
                        ? issueInput.value
                        : "",

                description:
                    descriptionInput
                        ? descriptionInput
                            .value
                            .trim()
                        : "",

                contactMethod:
                    contactMethodInput
                        ? contactMethodInput.value
                        : "WhatsApp"

            };


            try {

                const response =
                    await fetch(
                        "/api/repairs",
                        {

                            method:
                                "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body:
                                JSON.stringify(
                                    repairRequest
                                )

                        }
                    );


                let data;


                try {

                    data =
                        await response.json();

                } catch (error) {

                    throw new Error(
                        "The server returned an invalid response."
                    );
                }


                if (!response.ok) {

                    throw new Error(
                        data.message ||
                        "Unable to submit repair request."
                    );
                }


                if (!data.repairId) {

                    throw new Error(
                        "Repair request was submitted, but no Repair ID was returned."
                    );
                }


                sessionStorage.setItem(
                    "lastRepairId",
                    data.repairId
                );


                if (generatedRepairId) {

                    generatedRepairId.textContent =
                        data.repairId;
                }


                repairForm.style.display =
                    "none";


                if (successMessage) {

                    successMessage.style.display =
                        "block";


                    successMessage.scrollIntoView({

                        behavior:
                            "smooth",

                        block:
                            "center"

                    });
                }


                console.log(
                    "Repair submitted successfully."
                );


                console.log(
                    "Repair ID:",
                    data.repairId
                );


            } catch (error) {

                console.error(
                    "Repair submission error:",
                    error
                );


                alert(
                    error.message ||
                    "Unable to submit your repair request. Please try again."
                );


            } finally {

                submitButton.disabled =
                    false;


                submitButton.textContent =
                    originalButtonText;
            }
        }
    );
}


/* =====================================================
   COPY REPAIR ID
===================================================== */

if (copyRepairId) {

    copyRepairId.addEventListener(
        "click",
        async function() {

            const repairId =
                generatedRepairId
                    ? generatedRepairId
                        .textContent
                        .trim()
                    : "";


            if (!repairId) {
                return;
            }


            try {

                await navigator.clipboard
                    .writeText(
                        repairId
                    );


                copyRepairId.textContent =
                    "✓ Copied!";


                setTimeout(
                    function() {

                        copyRepairId.textContent =
                            "Copy Repair ID";

                    },
                    2000
                );


            } catch (error) {

                console.error(
                    "Unable to copy ID:",
                    error
                );


                alert(
                    "Repair ID: " +
                    repairId
                );
            }
        }
    );
}


/* =====================================================
   BOOK ANOTHER REPAIR
===================================================== */

if (newRepairBtn) {

    newRepairBtn.addEventListener(
        "click",
        function() {

            sessionStorage.removeItem(
                "lastRepairId"
            );


            if (successMessage) {

                successMessage.style.display =
                    "none";
            }


            if (generatedRepairId) {

                generatedRepairId.textContent =
                    "";
            }


            if (repairForm) {

                repairForm.reset();

                repairForm.style.display =
                    "grid";


                const submitButton =
                    repairForm.querySelector(
                        ".booking-btn"
                    );


                if (submitButton) {

                    submitButton.disabled =
                        false;


                    submitButton.textContent =
                        "Submit Repair Request";
                }
            }


            window.location.hash =
                "booking";
        }
    );
}


/* =====================================================
   RESTORE REPAIR ID AFTER REFRESH
===================================================== */

window.addEventListener(
    "DOMContentLoaded",
    function() {

        const savedRepairId =
            sessionStorage.getItem(
                "lastRepairId"
            );


        if (
            savedRepairId &&
            repairForm &&
            successMessage &&
            generatedRepairId
        ) {

            generatedRepairId.textContent =
                savedRepairId;


            repairForm.style.display =
                "none";


            successMessage.style.display =
                "block";
        }
    }
);


/* =====================================================
   TRACK REPAIR ELEMENTS
===================================================== */

const trackRepairBtn =
    document.getElementById(
        "trackRepairBtn"
    );

const trackRepairId =
    document.getElementById(
        "trackRepairId"
    );

const trackingResult =
    document.getElementById(
        "trackingResult"
    );

const trackError =
    document.getElementById(
        "trackError"
    );


/* =====================================================
   TRACK REPAIR
===================================================== */

if (
    trackRepairBtn &&
    trackRepairId
) {

    trackRepairBtn.addEventListener(
        "click",
        async function() {

            const enteredId =
                trackRepairId
                    .value
                    .trim()
                    .toUpperCase();


            if (!enteredId) {

                if (trackError) {

                    trackError.textContent =
                        "Please enter your Repair ID.";


                    trackError.style.display =
                        "block";
                }


                if (trackingResult) {

                    trackingResult.style.display =
                        "none";
                }


                return;
            }


            trackRepairBtn.disabled =
                true;


            trackRepairBtn.textContent =
                "Checking...";


            try {

                const response =
                    await fetch(
                        `/api/repairs/${encodeURIComponent(
                            enteredId
                        )}`
                    );


                let data;


                try {

                    data =
                        await response.json();

                } catch (error) {

                    throw new Error(
                        "The server returned an invalid response."
                    );
                }


                if (!response.ok) {

                    throw new Error(
                        data.message ||
                        "Repair request not found."
                    );
                }


                const repair =
                    data.repair;


                if (!repair) {

                    throw new Error(
                        "Repair information was not returned."
                    );
                }


                if (trackError) {

                    trackError.style.display =
                        "none";
                }


                if (trackingResult) {

                    trackingResult.style.display =
                        "block";
                }


                const trackedId =
                    document.getElementById(
                        "trackedId"
                    );


                const trackedDevice =
                    document.getElementById(
                        "trackedDevice"
                    );


                const trackedIssue =
                    document.getElementById(
                        "trackedIssue"
                    );


                const trackedDate =
                    document.getElementById(
                        "trackedDate"
                    );


                const trackedStatus =
                    document.getElementById(
                        "trackedStatus"
                    );


                if (trackedId) {

                    trackedId.textContent =
                        repair.repairId || "";
                }


                if (trackedDevice) {

                    trackedDevice.textContent =
                        `${repair.brand || ""} ${repair.model || ""}`
                            .trim();
                }


                if (trackedIssue) {

                    trackedIssue.textContent =
                        repair.issue || "";
                }


                if (trackedDate) {

                    trackedDate.textContent =
                        formatRepairDate(
                            repair.createdAt
                        );
                }


                if (trackedStatus) {

                    trackedStatus.textContent =
                        repair.status || "";
                }


                updateRepairProgress(
                    repair.status
                );


                if (trackingResult) {

                    trackingResult
                        .scrollIntoView({

                            behavior:
                                "smooth",

                            block:
                                "center"

                        });
                }


            } catch (error) {

                console.error(
                    "Tracking error:",
                    error
                );


                if (trackingResult) {

                    trackingResult.style.display =
                        "none";
                }


                if (trackError) {

                    trackError.textContent =
                        error.message ||
                        "Repair ID not found. Please check the ID and try again.";


                    trackError.style.display =
                        "block";
                }


            } finally {

                trackRepairBtn.disabled =
                    false;


                trackRepairBtn.textContent =
                    "Track Repair";
            }
        }
    );
}


/* =====================================================
   PRESS ENTER TO TRACK
===================================================== */

if (
    trackRepairId &&
    trackRepairBtn
) {

    trackRepairId.addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter"
            ) {

                event.preventDefault();

                trackRepairBtn.click();
            }
        }
    );
}


/* =====================================================
   FORMAT REPAIR DATE
===================================================== */

function formatRepairDate(
    dateValue
) {

    if (!dateValue) {
        return "";
    }


    const parsedDate =
        new Date(
            dateValue
                .replace(
                    " ",
                    "T"
                )
        );


    if (
        Number.isNaN(
            parsedDate.getTime()
        )
    ) {

        return dateValue;
    }


    return parsedDate
        .toLocaleString(
            "en-NG",
            {
                dateStyle:
                    "medium",

                timeStyle:
                    "short"
            }
        );
}


/* =====================================================
   UPDATE REPAIR PROGRESS
===================================================== */

function updateRepairProgress(
    status
) {

    const statuses = [

        "Request Received",

        "Device Inspection",

        "Repair In Progress",

        "Ready for Collection"

    ];


    const currentIndex =
        statuses.indexOf(
            status
        );


    const steps = [

        document.getElementById(
            "stepReceived"
        ),

        document.getElementById(
            "stepInspection"
        ),

        document.getElementById(
            "stepRepair"
        ),

        document.getElementById(
            "stepReady"
        )

    ];


    steps.forEach(
        function(step) {

            if (!step) {
                return;
            }


            step.classList.remove(
                "active",
                "completed"
            );
        }
    );


    if (
        currentIndex === -1
    ) {

        return;
    }


    steps.forEach(
        function(
            step,
            index
        ) {

            if (!step) {
                return;
            }


            if (
                index <= currentIndex
            ) {

                step.classList.add(
                    "active"
                );
            }


            if (
                index < currentIndex
            ) {

                step.classList.add(
                    "completed"
                );
            }
        }
    );
}

/* =====================================================
   SMOOTH NAVIGATION
===================================================== */

const navigationLinks =
    document.querySelectorAll(
        'a[href^="#"]'
    );


navigationLinks.forEach(
    function(link) {

        link.addEventListener(
            "click",
            function(event) {

                const targetId =
                    this.getAttribute(
                        "href"
                    );


                if (
                    !targetId ||
                    targetId === "#"
                ) {

                    return;
                }


                const targetSection =
                    document.querySelector(
                        targetId
                    );


                if (!targetSection) {
                    return;
                }


                event.preventDefault();


                /* =====================================
                   START A NEW REPAIR WHEN BOOK REPAIR
                   IS CLICKED
                ===================================== */

                if (
                    targetId === "#booking"
                ) {

                    sessionStorage.removeItem(
                        "lastRepairId"
                    );


                    if (successMessage) {

                        successMessage.style.display =
                            "none";
                    }


                    if (generatedRepairId) {

                        generatedRepairId.textContent =
                            "";
                    }


                    if (repairForm) {

                        repairForm.style.display =
                            "grid";


                        const submitButton =
                            repairForm.querySelector(
                                ".booking-btn"
                            );


                        if (submitButton) {

                            submitButton.disabled =
                                false;


                            submitButton.textContent =
                                "Submit Repair Request";
                        }
                    }
                }


                targetSection
                    .scrollIntoView({

                        behavior:
                            "smooth",

                        block:
                            "start"

                    });

            }
        );
    }
);


/* =====================================================
   TRACK ORDER ELEMENTS
===================================================== */

const trackOrderBtn =
    document.getElementById(
        "trackOrderBtn"
    );

const trackOrderId =
    document.getElementById(
        "trackOrderId"
    );

const orderTrackingResult =
    document.getElementById(
        "orderTrackingResult"
    );

const orderTrackError =
    document.getElementById(
        "orderTrackError"
    );


/* =====================================================
   TRACK ORDER
===================================================== */

if (
    trackOrderBtn &&
    trackOrderId
) {

    trackOrderBtn.addEventListener(
        "click",
        async function() {

            const enteredId =
                trackOrderId
                    .value
                    .trim()
                    .toUpperCase();


            if (!enteredId) {

                if (orderTrackError) {

                    orderTrackError.textContent =
                        "Please enter your Order ID.";

                    orderTrackError.style.display =
                        "block";
                }


                if (orderTrackingResult) {

                    orderTrackingResult.style.display =
                        "none";
                }


                return;
            }


            trackOrderBtn.disabled =
                true;

            trackOrderBtn.textContent =
                "Checking...";


            try {

                const response =
                    await fetch(
                        `/api/orders/${encodeURIComponent(
                            enteredId
                        )}`
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.message ||
                        "Order not found."
                    );
                }


                const order =
                    data.order;


                if (!order) {

                    throw new Error(
                        "Order information was not returned."
                    );
                }


                if (orderTrackError) {

                    orderTrackError.style.display =
                        "none";
                }


                if (orderTrackingResult) {

                    orderTrackingResult.style.display =
                        "block";
                }


                const trackedOrderId =
                    document.getElementById(
                        "trackedOrderId"
                    );

                const trackedOrderStatus =
                    document.getElementById(
                        "trackedOrderStatus"
                    );

                const trackedOrderProduct =
                    document.getElementById(
                        "trackedOrderProduct"
                    );

                const trackedOrderQuantity =
                    document.getElementById(
                        "trackedOrderQuantity"
                    );

                const trackedOrderTotal =
                    document.getElementById(
                        "trackedOrderTotal"
                    );

                const trackedOrderCustomer =
                    document.getElementById(
                        "trackedOrderCustomer"
                    );

                const trackedOrderPhone =
                    document.getElementById(
                        "trackedOrderPhone"
                    );

                const trackedOrderDate =
                    document.getElementById(
                        "trackedOrderDate"
                    );


                if (trackedOrderId) {

                    trackedOrderId.textContent =
                        order.orderId || "";
                }


                if (trackedOrderStatus) {

                    trackedOrderStatus.textContent =
                        order.status || "";
                }


                if (trackedOrderProduct) {

                    trackedOrderProduct.textContent =
                        order.productName || "";
                }


                if (trackedOrderQuantity) {

                    trackedOrderQuantity.textContent =
                        order.quantity || 0;
                }


                if (trackedOrderTotal) {

                    trackedOrderTotal.textContent =
                        `₦${formatProductPrice(
                            order.totalPrice || 0
                        )}`;
                }


                if (trackedOrderCustomer) {

                    trackedOrderCustomer.textContent =
                        order.customerName || "";
                }


                if (trackedOrderPhone) {

                    trackedOrderPhone.textContent =
                        order.phone || "";
                }


                if (trackedOrderDate) {

                    trackedOrderDate.textContent =
                        formatOrderDate(
                            order.createdAt
                        );
                }


                updateOrderProgress(
                    order.status
                );


                if (orderTrackingResult) {

                    orderTrackingResult.scrollIntoView({

                        behavior:
                            "smooth",

                        block:
                            "center"

                    });
                }


            } catch (error) {

                console.error(
                    "Order tracking error:",
                    error
                );


                if (orderTrackingResult) {

                    orderTrackingResult.style.display =
                        "none";
                }


                if (orderTrackError) {

                    orderTrackError.textContent =
                        error.message ||
                        "Order ID not found.";

                    orderTrackError.style.display =
                        "block";
                }


            } finally {

                trackOrderBtn.disabled =
                    false;

                trackOrderBtn.textContent =
                    "Track Order";
            }
        }
    );
}


/* =====================================================
   PRESS ENTER TO TRACK ORDER
===================================================== */

if (
    trackOrderId &&
    trackOrderBtn
) {

    trackOrderId.addEventListener(
        "keydown",
        function(event) {

            if (
                event.key === "Enter"
            ) {

                event.preventDefault();

                trackOrderBtn.click();
            }
        }
    );
}


/* =====================================================
   FORMAT ORDER DATE
===================================================== */

function formatOrderDate(
    dateValue
) {

    if (!dateValue) {
        return "";
    }


    const parsedDate =
        new Date(
            dateValue.replace(
                " ",
                "T"
            )
        );


    if (
        Number.isNaN(
            parsedDate.getTime()
        )
    ) {

        return dateValue;
    }


    return parsedDate.toLocaleString(
        "en-NG",
        {
            dateStyle:
                "medium",

            timeStyle:
                "short"
        }
    );
}


/* =====================================================
   UPDATE ORDER PROGRESS
===================================================== */

function updateOrderProgress(
    status
) {

    const statuses = [

        "Pending",

        "Confirmed",

        "Ready",

        "Completed"

    ];


    const steps = [

        document.getElementById(
            "orderStepPending"
        ),

        document.getElementById(
            "orderStepConfirmed"
        ),

        document.getElementById(
            "orderStepReady"
        ),

        document.getElementById(
            "orderStepCompleted"
        )

    ];


    steps.forEach(
        function(step) {

            if (!step) {
                return;
            }


            step.classList.remove(
                "active",
                "completed"
            );
        }
    );


    if (
        status === "Cancelled"
    ) {

        const badge =
            document.getElementById(
                "trackedOrderStatus"
            );


        if (badge) {

            badge.textContent =
                "Cancelled";
        }


        return;
    }


    const currentIndex =
        statuses.indexOf(
            status
        );


    if (
        currentIndex === -1
    ) {

        return;
    }


    steps.forEach(
        function(
            step,
            index
        ) {

            if (!step) {
                return;
            }


            if (
                index <= currentIndex
            ) {

                step.classList.add(
                    "active"
                );
            }


            if (
                index < currentIndex
            ) {

                step.classList.add(
                    "completed"
                );
            }
        }
    );
}


/* =====================================================
   ACCESSORIES ELEMENTS
===================================================== */

const accessoriesGrid =
    document.getElementById(
        "accessoriesGrid"
    );

const emptyProductsMessage =
    document.getElementById(
        "emptyProductsMessage"
    );


/* =====================================================
   LOAD ACCESSORIES FROM DATABASE
===================================================== */

async function loadAccessories() {

    if (!accessoriesGrid) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/products"
            );


        let data;


        try {

            data =
                await response.json();

        } catch (error) {

            throw new Error(
                "The product server returned an invalid response."
            );
        }


        if (!response.ok) {

            throw new Error(
                data.message ||
                "Unable to load accessories."
            );
        }


        const products =
            data.products || [];


        window.corefixProducts =
            products;


        accessoriesGrid.innerHTML =
            "";


        /* =============================================
           NO PRODUCTS
        ============================================= */

        if (
            products.length === 0
        ) {

            if (emptyProductsMessage) {

                emptyProductsMessage.textContent =
                    "No accessories are available right now.";


                emptyProductsMessage.style.display =
                    "block";
            }


            return;
        }


        if (emptyProductsMessage) {

            emptyProductsMessage.style.display =
                "none";
        }


        /* =============================================
           CREATE PRODUCT CARDS
        ============================================= */

        products.forEach(
            function(product) {

                const card =
                    document.createElement(
                        "article"
                    );


                card.className =
                    "product-card";


                const isOutOfStock =
                    product.stockStatus ===
                    "Out of Stock";


                let stockClass =
                    "stock-in";


                if (
                    product.stockStatus ===
                    "Low Stock"
                ) {

                    stockClass =
                        "stock-low";
                }


                if (isOutOfStock) {

                    stockClass =
                        "stock-out";
                }


                /* =====================================
                   PRODUCT VISUAL
                ===================================== */

                let productVisual = `

                    <div class="product-icon">

                        ${escapeProductHTML(
                            product.icon || "📦"
                        )}

                    </div>

                `;


                if (
                    product.image &&
                    product.image.trim() !== ""
                ) {

                    const imageUrl =
                        product.image.startsWith("http://") ||
                        product.image.startsWith("https://")
                            ? product.image
                            : `/static/assets/products/${encodeURIComponent(
                                product.image
                            )}`;


                    productVisual = `

                        <div class="product-image-wrapper">

                            <img
                                src="${escapeProductHTML(
                                    imageUrl
                                )}"
                                alt="${escapeProductHTML(
                                    product.name
                                )}"
                                class="product-image"
                                loading="lazy"
                            >

                        </div>

                    `;
                }


                /* =====================================
                   PRODUCT CARD
                ===================================== */

                card.innerHTML = `

                    <div class="product-card-media">

                        ${productVisual}


                        <span
                            class="
                                product-stock
                                ${stockClass}
                            "
                        >

                            ${escapeProductHTML(
                                product.stockStatus ||
                                "In Stock"
                            )}

                        </span>

                    </div>


                    <div class="product-card-content">

                        <div class="product-card-heading">

                            <h3>

                                ${escapeProductHTML(
                                    product.name
                                )}

                            </h3>

                        </div>


                        <p class="product-description">

                            ${escapeProductHTML(
                                product.description
                            )}

                        </p>


                        <div class="product-bottom">

                            <div class="product-price-wrap">

                                <span class="product-price-label">
                                    Price
                                </span>


                                <span class="product-price">

                                    ₦${formatProductPrice(
                                        product.price
                                    )}

                                </span>

                            </div>


                            <button
                                type="button"
                                class="order-btn"
                                data-id="${product.id}"

                                data-product="${escapeProductHTML(
                                    product.name
                                )}"

                                data-price="₦${formatProductPrice(
                                    product.price
                                )}"

                                ${
                                    isOutOfStock
                                        ? "disabled"
                                        : ""
                                }
                            >

                                ${
                                    isOutOfStock
                                        ? "Out of Stock"
                                        : "Order Now"
                                }

                            </button>

                        </div>

                    </div>

                `;


                accessoriesGrid
                    .appendChild(
                        card
                    );
            }
        );


        /* =============================================
           ACTIVATE ORDER BUTTONS
        ============================================= */

        addAccessoryOrderListeners();


    } catch (error) {

        console.error(
            "Accessory loading error:",
            error
        );


        accessoriesGrid.innerHTML =
            "";


        if (emptyProductsMessage) {

            emptyProductsMessage.textContent =
                error.message ||
                "Unable to load accessories right now.";


            emptyProductsMessage.style.display =
                "block";
        }
    }
}

/* =====================================================
   ORDER MODAL ELEMENTS
===================================================== */

const orderModal =
    document.getElementById(
        "orderModal"
    );

const orderModalOverlay =
    document.getElementById(
        "orderModalOverlay"
    );

const orderModalClose =
    document.getElementById(
        "orderModalClose"
    );

const orderForm =
    document.getElementById(
        "orderForm"
    );

const orderFormContent =
    document.getElementById(
        "orderFormContent"
    );

const orderProductId =
    document.getElementById(
        "orderProductId"
    );

const orderProductName =
    document.getElementById(
        "orderProductName"
    );

const orderProductPrice =
    document.getElementById(
        "orderProductPrice"
    );

const orderCustomerName =
    document.getElementById(
        "orderCustomerName"
    );

const orderPhone =
    document.getElementById(
        "orderPhone"
    );

const orderQuantity =
    document.getElementById(
        "orderQuantity"
    );

const orderTotalPrice =
    document.getElementById(
        "orderTotalPrice"
    );

const orderError =
    document.getElementById(
        "orderError"
    );

const orderSuccess =
    document.getElementById(
        "orderSuccess"
    );

const generatedOrderId =
    document.getElementById(
        "generatedOrderId"
    );

const successfulOrderProduct =
    document.getElementById(
        "successfulOrderProduct"
    );

const successfulOrderQuantity =
    document.getElementById(
        "successfulOrderQuantity"
    );

const successfulOrderTotal =
    document.getElementById(
        "successfulOrderTotal"
    );

const orderDoneBtn =
    document.getElementById(
        "orderDoneBtn"
    );


let selectedOrderProduct = null;


/* =====================================================
   ACCESSORY ORDER BUTTONS
===================================================== */

function addAccessoryOrderListeners() {

    const orderButtons =
        document.querySelectorAll(
            ".order-btn"
        );


    orderButtons.forEach(
        function(button) {

            if (button.disabled) {
                return;
            }


            button.addEventListener(
                "click",
                function() {

                    const productId =
                        Number(
                            this.dataset.id
                        );


                    const product =
                        window.corefixProducts
                            ? window.corefixProducts.find(
                                item =>
                                    Number(item.id) ===
                                    productId
                            )
                            : null;


                    if (!product) {

                        alert(
                            "Unable to load this product."
                        );

                        return;
                    }


                    openOrderModal(
                        product
                    );

                }
            );

        }
    );

}


/* =====================================================
   OPEN ORDER MODAL
===================================================== */

function openOrderModal(
    product
) {

    if (!orderModal) {
        return;
    }


    selectedOrderProduct =
        product;


    if (orderProductId) {

        orderProductId.value =
            product.id;
    }


    if (orderProductName) {

        orderProductName.textContent =
            product.name;
    }


    if (orderProductPrice) {

        orderProductPrice.textContent =
            `₦${formatProductPrice(
                product.price
            )}`;
    }


    if (orderQuantity) {

        orderQuantity.value =
            1;
    }


    if (orderCustomerName) {

        orderCustomerName.value =
            "";
    }


    if (orderPhone) {

        orderPhone.value =
            "";
    }


    if (orderError) {

        orderError.textContent =
            "";

        orderError.style.display =
            "none";
    }


    if (orderFormContent) {

        orderFormContent.style.display =
            "block";
    }


    if (orderSuccess) {

        orderSuccess.style.display =
            "none";
    }


    updateOrderTotal();


    orderModal.classList.add(
        "active"
    );


    orderModal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.classList.add(
        "modal-open"
    );


    if (orderCustomerName) {

        setTimeout(
            function() {

                orderCustomerName.focus();

            },
            100
        );
    }

}


/* =====================================================
   CLOSE ORDER MODAL
===================================================== */

function closeOrderModal() {

    if (!orderModal) {
        return;
    }


    orderModal.classList.remove(
        "active"
    );


    orderModal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.classList.remove(
        "modal-open"
    );


    selectedOrderProduct =
        null;


    if (orderForm) {

        orderForm.reset();
    }


    if (orderError) {

        orderError.style.display =
            "none";
    }

}


/* =====================================================
   CLOSE MODAL EVENTS
===================================================== */

if (orderModalClose) {

    orderModalClose.addEventListener(
        "click",
        closeOrderModal
    );
}


if (orderModalOverlay) {

    orderModalOverlay.addEventListener(
        "click",
        closeOrderModal
    );
}


if (orderDoneBtn) {

    orderDoneBtn.addEventListener(
        "click",
        closeOrderModal
    );
}


document.addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Escape" &&
            orderModal &&
            orderModal.classList.contains(
                "active"
            )
        ) {

            closeOrderModal();

        }

    }
);


/* =====================================================
   UPDATE ORDER TOTAL
===================================================== */

function updateOrderTotal() {

    if (
        !selectedOrderProduct ||
        !orderTotalPrice
    ) {

        return;
    }


    let quantity =
        Number(
            orderQuantity
                ? orderQuantity.value
                : 1
        );


    if (
        Number.isNaN(quantity) ||
        quantity < 1
    ) {

        quantity = 1;
    }


    const total =
        Number(
            selectedOrderProduct.price
        ) * quantity;


    orderTotalPrice.textContent =
        `₦${formatProductPrice(
            total
        )}`;

}


if (orderQuantity) {

    orderQuantity.addEventListener(
        "input",
        updateOrderTotal
    );
}


/* =====================================================
   SUBMIT ORDER
===================================================== */

if (orderForm) {

    orderForm.addEventListener(
        "submit",
        async function(event) {

            event.preventDefault();


            if (!selectedOrderProduct) {

                return;
            }


            const submitButton =
                orderForm.querySelector(
                    ".order-submit-btn"
                );


            const customerName =
                orderCustomerName
                    ? orderCustomerName.value.trim()
                    : "";


            const phone =
                orderPhone
                    ? orderPhone.value.trim()
                    : "";


            const quantity =
                Number(
                    orderQuantity
                        ? orderQuantity.value
                        : 1
                );


            if (!customerName) {

                showOrderError(
                    "Please enter your name."
                );

                return;
            }


            if (!phone) {

                showOrderError(
                    "Please enter your phone number."
                );

                return;
            }


            if (
                Number.isNaN(quantity) ||
                quantity < 1
            ) {

                showOrderError(
                    "Quantity must be at least 1."
                );

                return;
            }


            if (submitButton) {

                submitButton.disabled =
                    true;

                submitButton.textContent =
                    "Placing Order...";
            }


            if (orderError) {

                orderError.style.display =
                    "none";
            }


            try {

                const response =
                    await fetch(
                        "/api/orders",
                        {

                            method:
                                "POST",

                            headers: {

                                "Content-Type":
                                    "application/json"

                            },

                            body:
                                JSON.stringify({

                                    productId:
                                        selectedOrderProduct.id,

                                    customerName:
                                        customerName,

                                    phone:
                                        phone,

                                    quantity:
                                        quantity

                                })

                        }
                    );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.message ||
                        "Unable to place order."
                    );
                }


                if (orderFormContent) {

                    orderFormContent.style.display =
                        "none";
                }


                if (orderSuccess) {

                    orderSuccess.style.display =
                        "block";
                }


                if (generatedOrderId) {

                    generatedOrderId.textContent =
                        data.orderId || "";
                }


                if (successfulOrderProduct) {

                    successfulOrderProduct.textContent =
                        data.productName ||
                        selectedOrderProduct.name;
                }


                if (successfulOrderQuantity) {

                    successfulOrderQuantity.textContent =
                        data.quantity ||
                        quantity;
                }


                if (successfulOrderTotal) {

                    successfulOrderTotal.textContent =
                        `₦${formatProductPrice(
                            data.totalPrice || 0
                        )}`;
                }


            } catch (error) {

                console.error(
                    "Order error:",
                    error
                );


                showOrderError(
                    error.message ||
                    "Unable to place order."
                );


            } finally {

                if (submitButton) {

                    submitButton.disabled =
                        false;

                    submitButton.textContent =
                        "Place Order";
                }
            }

        }
    );

}


/* =====================================================
   SHOW ORDER ERROR
===================================================== */

function showOrderError(
    message
) {

    if (!orderError) {
        return;
    }


    orderError.textContent =
        message;


    orderError.style.display =
        "block";

}


/* =====================================================
   FORMAT PRODUCT PRICE
===================================================== */

function formatProductPrice(
    price
) {

    const numericPrice =
        Number(
            price || 0
        );


    if (
        Number.isNaN(
            numericPrice
        )
    ) {

        return "0";
    }


    return numericPrice
        .toLocaleString(
            "en-NG"
        );
}


/* =====================================================
   ESCAPE PRODUCT HTML
===================================================== */

function escapeProductHTML(
    value
) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =====================================================
   START ACCESSORIES
===================================================== */

loadAccessories();


/* =====================================================
   MOBILE NAVIGATION
===================================================== */

const mobileMenuBtn =
    document.getElementById(
        "mobileMenuBtn"
    );

const mainNav =
    document.getElementById(
        "mainNav"
    );


if (
    mobileMenuBtn &&
    mainNav
) {

    /* OPEN / CLOSE MENU */

    mobileMenuBtn.addEventListener(
        "click",
        function() {

            const isOpen =
                mainNav.classList.toggle(
                    "active"
                );

            mobileMenuBtn.classList.toggle(
                "active",
                isOpen
            );

            mobileMenuBtn.setAttribute(
                "aria-expanded",
                isOpen
                    ? "true"
                    : "false"
            );

            mobileMenuBtn.setAttribute(
                "aria-label",
                isOpen
                    ? "Close navigation menu"
                    : "Open navigation menu"
            );

        }
    );


    /* CLOSE MENU AFTER CLICKING A LINK */

    const mobileNavLinks =
        mainNav.querySelectorAll(
            "a"
        );


    mobileNavLinks.forEach(
        function(link) {

            link.addEventListener(
                "click",
                function() {

                    mainNav.classList.remove(
                        "active"
                    );

                    mobileMenuBtn.classList.remove(
                        "active"
                    );

                    mobileMenuBtn.setAttribute(
                        "aria-expanded",
                        "false"
                    );

                }
            );

        }
    );


    /* CLOSE MENU WHEN SCREEN RETURNS TO DESKTOP */

    window.addEventListener(
        "resize",
        function() {

            if (
                window.innerWidth > 900
            ) {

                mainNav.classList.remove(
                    "active"
                );

                mobileMenuBtn.classList.remove(
                    "active"
                );

                mobileMenuBtn.setAttribute(
                    "aria-expanded",
                    "false"
                );

            }

        }
    );

}


// =====================================================
// COREFIX PWA INSTALL
// =====================================================

let deferredInstallPrompt = null;


// Chrome says the app can be installed
window.addEventListener("beforeinstallprompt", event => {

    event.preventDefault();

    deferredInstallPrompt = event;

    const installAppBtn =
        document.getElementById("installAppBtn");

    if (installAppBtn) {
        installAppBtn.hidden = false;
    }

});


// Wait until the HTML is ready
document.addEventListener("DOMContentLoaded", () => {

    const installAppBtn =
        document.getElementById("installAppBtn");

    if (!installAppBtn) {
        console.log("CoreFix install button not found.");
        return;
    }

    installAppBtn.addEventListener("click", async () => {

        if (!deferredInstallPrompt) {
            console.log("Install prompt is not available.");
            return;
        }

        deferredInstallPrompt.prompt();

        const result =
            await deferredInstallPrompt.userChoice;

        console.log(
            "CoreFix install choice:",
            result.outcome
        );

        deferredInstallPrompt = null;

        installAppBtn.hidden = true;

    });

});


window.addEventListener("appinstalled", () => {

    console.log("CoreFix installed successfully.");

    deferredInstallPrompt = null;

    const installAppBtn =
        document.getElementById("installAppBtn");

    if (installAppBtn) {
        installAppBtn.hidden = true;
    }

});
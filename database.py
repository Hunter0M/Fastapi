import psycopg2


# from app import db

# host='localhost'
# database='myduka'
# user='postgres'
# password='0777'
# port='5432'

# conecting to the PostgreSQL database
conn=psycopg2.connect(
    dbname='inventory_system',
    user='postgres',
    password='0777',
    host='localhost',
    port=5432
)
# # open a cursor to perfom database operation

cur = conn.cursor()

# to display products

# def get_products():
#     cur.execute('select * from products;')
#     prods=cur.fetchall()
#     for i in prods:
#         print(i)
# # get_products()


# to display sales 

# def get_sales():
#     select="select * from sales;"
#     cur.execute(select)
#     sales=cur.fetchall()
#     for i in sales:
#         print(i) 
    


# def insert_products():
#     insert="""INSERT INTO products( name, buying_price, selling_price, stock_quantity) 
#       VALUES ('airpods', 5000, 6000,233);"""
#     cur.execute(insert)
#     conn.commit()

# # insert_products()

# def insert_sales():
#     insert="""INSERT INTO sales( pid, quantity, created_at) 
#       VALUES (5, 7,now());"""
#     cur.execute(insert)
#     conn.commit()
# insert_sales()
# get_sales()

# 
def get_data(table):
    select=f"select * from {table};"
    cur.execute(select)
    data=cur.fetchall()
    return data
    # for i in data:
    #     print(i)

# function to insert products 

# def insert_products(values):
#     insert=f"""INSERT INTO products( name, buying_price, selling_price, stock_quantity)values{values}"""
#     cur.execute(insert)
#     conn.commit()
# products_value=('Mobile_charger',2500,3000,9)
# insert_products(products_value)

def insert_products(values):
    # place holders (%s)
    insert="""INSERT INTO product( name, buying_price, selling_price, stock_quantity)values(%s,%s,%s,%s)"""
    cur.execute(insert,values)
    conn.commit()

# updating products
# def update_products(values):
#     update=""" UPDATE products SET  name=%s, buying_price=%s, selling_price=%s, stock_quantity=%s WHERE id=%s; """
#     cur.execute(update,values)
#     conn.commit()
    

# products_value=('laptop_charger',2500,3000,9)

# insert_products(products_value)


# function to insert sales 
 
# def insert_sales(values):
#     insert=f"""INSERT INTO sales( pid, quantity, created_at)values{values},now()"""
#     cur.execute(insert)
#     conn.commit()
# sales_value=(12,14)
# insert_products(sales_value)
# get_data("products")
# get_data("sales")

def insert_sales(values):
    insert="""INSERT INTO sales( pid, quantity, created_at)values(%s,%s,now());"""
    cur.execute(insert,values)
    conn.commit()
# sales_values=(4,13)
# insert_sales(sales_values)
    
    # function to display every sale 
def display_sales():
    display="select product.product_name, sum(selling_price*quantity) \
    as result from product join sales on sales.pid=product.id group by product.product_name;"
    cur.execute(display)
    data=cur.fetchall()
    return data

# display sales by name of the products
def products_name(a):
    p_name='select p.product_name from product as p where id=%s;'
    cur.execute(p_name,(a,))
    data=cur.fetchone()
    return data

# Editing a products
# def edit_products(values ,cur,conn):
#     edit_query = 'UPDATE products SET name=%s, buying_price=%s, selling_price=%s, stock_quantity=%s WHERE id=%s ;'
#     assert len(values) == 5, "Incorrect number of elements in values tuple"
#     cur.execute(edit_query, values)
#     row_count = cur.rowcount
#     return(row_count)
#     conn.commit()


# deleting a products
# def delete_product(product_id, cur, conn):
#     delete_query = 'DELETE FROM product WHERE id = %s;'
#     cur.execute(delete_query, (product_id,))
#     # len cur
#     row_count = cur.rowcount
#     conn.commit()
#     return row_count

    

# qaurry for display a massage out of range 
def sales_out_of(o):
    out_of=' select * from sales where quantity not between 100 and 150;'
    cur.execute(out_of,(o,))
    data=cur.fetchall()
    return data




# display_sales()

# function to display total profit
def display_profit():
    display="select p.product_name,sum(((selling_price-buying_price)*quantity))\
          as profit from product as p join sales as s on s.pid=p.id group by p.product_name;"
    cur.execute(display)
    data=cur.fetchall()
    
    return data


# function to display total profits
def Total_profit():
    dis_pro=" select round(sum(((selling_price-buying_price)*quantity)),2) \
        as profit from product as p join sales as s on s.pid=p.id;"
    cur.execute(dis_pro)
    data=cur.fetchall()

    return data

# calculating total sales to display as one
def display_sum_sales():
    dis_sum= "SELECT SUM(selling_price*quantity) AS total_sales FROM product as p join sales as s on s.pid=p.id ;"
    cur.execute(dis_sum)
    data=cur.fetchall()
    return data

# display sales per day 

def display_sum_sales_today():
    total_sales= "SELECT date(created_at) as today_date,SUM((selling_price)*quantity) AS total_sales_for_today FROM product as p\
          join sales as s on s.pid=p.id WHERE date(created_at) = CURRENT_DATE group by today_date;"
    cur.execute(total_sales)
    data=cur.fetchall()
    return data

# display sales per day
def day_sales():
    d_sales=" SELECT DATE(created_at) AS date_only,sum((selling_price)*quantity)as total \
        from sales as s join product as p on p.id=s.pid group by date_only order by date_only;"
    cur.execute(d_sales)
    data=cur.fetchall()
    return data

#  display profit per day 
def pro_per_day():
    d_profit=" SELECT DATE(created_at) AS date_only,sum(selling_price-buying_price)as profits from sales as s join product as p on p.id=s.pid group by date_only order by date_only;"
    cur.execute(d_profit)
    data=cur.fetchall()
    return data

# Function to display profit for today
def pro_for_today():
    profit_today="SELECT TO_CHAR(CURRENT_DATE, 'YYYY/MM/DD') AS date_only,round(sum(selling_price-buying_price),2)\
        as profits from sales as s join product as p on p.id=s.pid group by date_only order by date_only limit 1;"
    cur.execute(profit_today)
    data=cur.fetchall()
    return data


# This query calculates the remaining stock for each product
def get_remaining_stock_per_product():
    query = """
            SELECT p.product_name, stock_quantity - COALESCE(SUM(s.quantity), 0)
            as remaining_stock FROM product as p LEFT JOIN sales as s on p.id = s.pid
            GROUP BY p.id, p.product_name, stock_quantity ORDER BY 
            remaining_stock DESC;
            """
    cur.execute(query)
    result =cur.fetchall()
    return result


 # This query returns the recent sales
# def get_recent_sales(): 
#     recent_sales=""" SELECT sales.id, sales.quantity * product.selling_price as total_
#                         amount FROM sales JOIN product ON sales.pid = product.id;"""
#     cur.execute(recent_sales)
#     result=cur.fetchall()
#     return result


def register_user(values):
    insert="insert into users(full_name,email,password)values(%s,%s,%s)"
    cur.execute(insert,values)
    conn.commit()

def check_email(email):
    query='select exists(select 1 from users where email=%s)'
    cur.execute(query,(email,))
    exist=cur.fetchone()[0]
    return exist

def check_login(email,password):
    query='select id,full_name from users where email=%s and password=%s '
    cur.execute(query,(email,password,))
    result=cur.fetchone()
    return result

def delete_record():
    delete="DELETE FROM product WHERE id=%s"
    cur.execute(delete)
    conn.commit()


# profile form
    
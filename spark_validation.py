'''
Example Schema Validation
Assumes the DataFrame `df` is already populated with schema:
{id : int, day_cd : 8-digit code representing date, category : varchar(24), type : varchar(10), ind : varchar(1), purchase_amt : decimal(18,6) }
Runs various checks to ensure data is valid (e.g. no NULL id and day_cd fields) and schema is valid (e.g. [category] cannot be larger than varchar(24))
'''

#
# Check if id or day_cd is null (i.e. rows are invalid if either of these two columsn are not integer)
#
NotValidCnt = 0
NotValidDF = df.filter("cast(id as integer) is null or cast(day_cd as integer) is null")
NotValidCnt = NotValidDF.count()

if (NotValidCnt > 0):
  # Filter out invalid data
  df = df.filter("cast(id as integer) is not null and cast(day_cd as integer) is not null")
  
  # Display Invalid data
  display(NotValidDF)



#
# Check for Duplicates
#. These four columns should uniqely identify each row and make up a unique clustered index in the underlying SQL database
#. thus df_dcnt = df_cnt if there are NO duplicates
#
df_cnt = df.count()
df_dcnt = df.select("id", "day_cd", "category", "type").distinct().count() 

# First pass remove duplicates if they exist
if (df_dcnt != df_cnt):
  print("Duplicate Data detected: rowcount: %s, distinct id: %s") % (df_cnt, df_dcnt)
  df = df.dropDuplicates()
  print("First pass dropping of duplicates")
  df_cnt = df.count()
  print("Restating df_cnt: %s") % df_cnt


#
# Check size of df data (integer, varchar(24), etc)
#

# Create temporary table
df.createOrReplaceTempView("df")

#  Build DataFrame checking the size of columns of df data
#.   Assumes a schema of {id : int, day_cd : 8-digit code representing date, category : varchar(24), type : varchar(10), ind : varchar(1), purchase_amt : decimal(18,6) }
checksize_df_sql = """
select 
min(cast(id as int)),
max(cast(id as int)),
min(length(day_cd)),
max(length(day_cd)),
max(length(category)),
max(length(type)),
max(length(ind)),
max(length(purchase_amt))
from df"""

# Create RDD of checksize_df
checksize_df = spark.sql(checksize_df_sql).rdd.map(lambda x: x).take(1)

#
# Checks
#   ALERT!: Will stop processing data because we do not have an automated mechanism to clear the data
#   ALERT: Will continue processing because we have automated mechanism to remove invalid rows
#

# id
if ((checksize_df[0][0] < 0) or (checksize_df[0][1] > 2147483647)): 
  raise ValueError("ALERT!: [id] values may be outside integer range")

# day_cd
if ((checksize_df[0][2] < 8) or (checksize_df[0][3] > 8)): 
  print("ALERT: [day_cd] values may be outside integer range, filtering out %s rows" % df.filter("length(day_cd) <> 8").count())
  df = df.filter("length(day_cd) == 8")

# category
if (checksize_df[0][4] > 24):
	raise ValueError("ALERT!: [category] outside varchar(24) range")

# type
if (checksize_df[0][5] > 10):
	raise ValueError("ALERT!: [type] outside varchar(10) range")

# ind
if (checksize_df[0][6] > 1):
 	print("ALERT: [ind] outside varchar(1) range, filtering out %s rows (if 0, previous filter removed these rows)" % df.filter("length(ind) <> 1").count())
 	df = df.filter("length(ind) == 1")

# purchase_amt
if (checksize_df[0][7] > 24):
	raise ValueError("ALERT!: [purchase_amt] outside [decimal](18, 6) range")


# Restating df_cnt
df.createOrReplaceTempView("df")
df_cnt = df.count()
print("Restating df_cnt: %s") % df_cnt
..

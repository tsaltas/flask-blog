"""empty message

Revision ID: 4bf695dd5bef
Revises: None
Create Date: 2014-08-19 18:34:53.092692

"""

# revision identifiers, used by Alembic.
revision = '4bf695dd5bef'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('author_id', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    """
    Shannon needs to work on this, automatic one with drop_column doesn't work
    # 1) Create new posts table without author_id
    op.create_table(
	    'new_posts',
	    Column('id', sa.INTEGER, sa.Sequence("post_id_sequence"), primary_key=True),
	    Column('title', sa.STRING(1024)),
	    Column('content', sa.TEXT),
	    Column('datetime', sa.DATETIME, server_default=datetime.datetime.now),
	    Column('author_id', sa.Integer, sa.ForeignKey('users.id')),
	)
	"""
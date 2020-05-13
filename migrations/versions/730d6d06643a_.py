"""empty message

Revision ID: 730d6d06643a
Revises: 
Create Date: 2020-05-12 22:53:56.821503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '730d6d06643a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('role', sa.String(length=20), nullable=True),
    sa.Column('seat', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_role'), 'user', ['role'], unique=False)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    op.create_table('game',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('host', sa.Integer(), nullable=False),
    sa.Column('template', sa.String(length=120), nullable=False),
    sa.Column('current_round', sa.String(length=120), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('start_time', sa.DateTime(), nullable=True),
    sa.Column('finish_time', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['host'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_game_finish_time'), 'game', ['finish_time'], unique=False)
    op.create_index(op.f('ix_game_name'), 'game', ['name'], unique=False)
    op.create_index(op.f('ix_game_start_time'), 'game', ['start_time'], unique=False)
    op.create_index(op.f('ix_game_template'), 'game', ['template'], unique=False)
    op.create_table('vote',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('seat', sa.Integer(), nullable=True),
    sa.Column('game_id', sa.Integer(), nullable=True),
    sa.Column('round', sa.String(length=120), nullable=True),
    sa.Column('vote_for', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vote_timestamp'), 'vote', ['timestamp'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_vote_timestamp'), table_name='vote')
    op.drop_table('vote')
    op.drop_index(op.f('ix_game_template'), table_name='game')
    op.drop_index(op.f('ix_game_start_time'), table_name='game')
    op.drop_index(op.f('ix_game_name'), table_name='game')
    op.drop_index(op.f('ix_game_finish_time'), table_name='game')
    op.drop_table('game')
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_role'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###

"""Added Audiogram and updated Visit

Revision ID: 22e6695387f0
Revises: 26dc6ce54448
Create Date: 2024-12-31 16:25:45.680148

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22e6695387f0'
down_revision = '26dc6ce54448'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('audiogram',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('visit_id', sa.Integer(), nullable=True),
    sa.Column('audiogram_date', sa.Date(), nullable=True),
    sa.Column('ul_250', sa.Integer(), nullable=True),
    sa.Column('ul_500', sa.Integer(), nullable=True),
    sa.Column('ul_1000', sa.Integer(), nullable=True),
    sa.Column('ul_2000', sa.Integer(), nullable=True),
    sa.Column('ul_3000', sa.Integer(), nullable=True),
    sa.Column('ul_4000', sa.Integer(), nullable=True),
    sa.Column('ul_6000', sa.Integer(), nullable=True),
    sa.Column('ul_8000', sa.Integer(), nullable=True),
    sa.Column('up_250', sa.Integer(), nullable=True),
    sa.Column('up_500', sa.Integer(), nullable=True),
    sa.Column('up_1000', sa.Integer(), nullable=True),
    sa.Column('up_2000', sa.Integer(), nullable=True),
    sa.Column('up_3000', sa.Integer(), nullable=True),
    sa.Column('up_4000', sa.Integer(), nullable=True),
    sa.Column('up_6000', sa.Integer(), nullable=True),
    sa.Column('up_8000', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['patient_id'], ['patient.id'], ),
    sa.ForeignKeyConstraint(['visit_id'], ['visit.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('audiogram', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_audiogram_patient_id'), ['patient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_audiogram_visit_id'), ['visit_id'], unique=False)

    with op.batch_alter_table('visit', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_visit_patient_id'), ['patient_id'], unique=False)
        batch_op.drop_column('up_500')
        batch_op.drop_column('up_8000')
        batch_op.drop_column('up_6000')
        batch_op.drop_column('up_3000')
        batch_op.drop_column('up_1000')
        batch_op.drop_column('up_2000')
        batch_op.drop_column('ul_500')
        batch_op.drop_column('ul_6000')
        batch_op.drop_column('up_250')
        batch_op.drop_column('ul_4000')
        batch_op.drop_column('ul_250')
        batch_op.drop_column('ul_3000')
        batch_op.drop_column('ul_8000')
        batch_op.drop_column('ul_2000')
        batch_op.drop_column('audiogram_date')
        batch_op.drop_column('ul_1000')
        batch_op.drop_column('up_4000')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('visit', schema=None) as batch_op:
        batch_op.add_column(sa.Column('up_4000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('ul_1000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('audiogram_date', sa.DATE(), nullable=True))
        batch_op.add_column(sa.Column('ul_2000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('ul_8000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('ul_3000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('ul_250', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('ul_4000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('up_250', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('ul_6000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('ul_500', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('up_2000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('up_1000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('up_3000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('up_6000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('up_8000', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('up_500', sa.INTEGER(), nullable=True))
        batch_op.drop_index(batch_op.f('ix_visit_patient_id'))

    with op.batch_alter_table('audiogram', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_audiogram_visit_id'))
        batch_op.drop_index(batch_op.f('ix_audiogram_patient_id'))

    op.drop_table('audiogram')
    # ### end Alembic commands ###
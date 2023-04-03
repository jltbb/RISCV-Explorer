class Instruction:
    def __init__(self, input_str):
        self.input_str = input_str
        self.sanitized_str = None
        self.opcode = None
        self.rs1 = None
        self.rs2 = None
        self.funct3 = None
        self.function = None
        self.rd = None
        self.ins30 = None
        self.funct7 = None
        self.imm = None
        self.type = None
    
    def sanitize_input(self):
        # Remove any spaces from the input string
        self.sanitized_str = self.input_str.replace(' ', '')
        
        # Check if the input string is a valid instruction word
        # We don't want anything other than 0's and 1's.
        valid_chars = '01'
        if not all(char in valid_chars for char in self.sanitized_str):
            raise ValueError('Input string is not a valid instruction word.')
    
    def extract_opcode(self):
        # Extract the last 7 bits from the instruction word
        self.opcode = self.sanitized_str[-7:]

    def extract_rd(self):
        if self.type != 'S-type' and self.type != 'B-type':
            self.rd = self.sanitized_str[-12:-7]
        else:
            # Given that we have a S-type instruction or B-type instruction
            # We do not have any RD bits.
            self.rd = None

    def extract_funct3(self):
        # Extract bits [-14, -12) from the instruction word
        self.funct3 = self.sanitized_str[-15:-12]

    def extract_rs1(self):
        # Extract the RS1 bits [19-15) from the instruction word
        self.rs1 = self.sanitized_str[-20:-15]

    def extract_rs2(self):
        # Extract the RS1 bits [24-20) from the instruction word
        if self.type != 'I-type':
            self.rs2 = self.sanitized_str[-25:-20]
        else:
            # Given that we have an I-type instruction
            # We do not have any RS2 bits.
            self.rs2 = None

    def extract_funct7(self):
        # Only R-type instructions have a funct7 field.
        if self.type == 'R-type':
            self.funct7 = self.sanitized_str[:-25]
        else:
            self.funct7 = None

    def extract_imm(self):
        if self.type == 'I-type':
            self.imm = self.sanitized_str[:-20]
        elif self.type == 'S-type':
            self.imm = self.sanitized_str[:-25] + self.sanitized_str[-12:-7]
        elif self.type == 'B-type':
            bit11 = self.sanitized_str[-8]
            bits4_1 = self.sanitized_str[-12:-8]
            bits10_5 = self.sanitized_str[-31:-25]
            bit12 = self.sanitized_str[-32]

            self.imm = bit12 + bits10_5 + bits4_1 + bit11

    def extract_ins30(self):
        self.ins30 = self.sanitized_str[-31]

    def determine_type(self):
        # Use a match statement to determine the type of instruction based on the opcode
        match self.opcode:
            case '0110011':
                self.type = 'R-type'
            case '0010011':
                self.type = 'I-type' # Immediates (addi, andi, etc)
            case '0000011':
                self.type = 'I-type' # Loads (lw)
            case '0100011':
                self.type = 'S-type'
            case '1100011':
                self.type = 'B-type'
            case _:
                self.type = 'Unknown type'
                raise ValueError('Input string is not a valid instruction word.')

    def determine_function(self):
        if self.type == 'R-type':
            r_type = {
                ('000', '0000000'): 'add',
                ('000', '0100000'): 'sub',
                ('001', '0000000'): 'sll',
                ('010', '0000000'): 'slt',
                ('011', '0000000'): 'sltu',
                ('100', '0000000'): 'xor',
                ('101', '0000000'): 'srl',
                ('101', '0100000'): 'sra',
                ('110', '0000000'): 'or',
                ('111', '0000000'): 'and'
            }
            self.function = r_type.get((self.funct3, self.funct7), 'unknown')
            
        elif self.type == 'I-type':
            i_type = {
                '000': 'addi',
                '001': 'slli',
                '010': 'slti',
                '011': 'sltiu',
                '100': 'xori',
                '110': 'ori',
                '111': 'andi',
                '000': 'lb',
                '001': 'lh',
                '010': 'lw',
                '100': 'lbu',
                '101': 'lhu'
            }
            self.function = i_type.get(self.funct3, 'unknown')

            # Handle the special case for srli and srai
            # These check funct7 values, however funct7
            # isn't really used for common I-types
            # so I have to handle this separately.
            if self.funct3 == '101':
                if self.sanitized_str[:-25] == '0000000':
                    self.function = 'srli'
                elif self.sanitized_str[:-25] == '0100000':
                    self.function = 'srai'

        elif self.type == 'S-type':
            s_type = {
                '010': 'sw'
            }
            self.function = s_type.get(self.funct3, 'unknown')

        elif self.type == 'B-type':
            b_type = {
                '000': 'beq',
                '101': 'bge',
                '100': 'blt',
                '001': 'bne',
            }
            self.function = b_type.get(self.funct3, 'unknown')

    @staticmethod
    def decimal(binary_str):
        if binary_str is not None:
            # We should use two's complement for values like imm
            # However we don't want to use it for the user input.
            # Check here for that
            max_num = 2 ** len(binary_str)
            if binary_str[0] == '1' and int(binary_str, 2) > 2 ** (len(binary_str)-1) and len(binary_str) != 32:
                return int(binary_str, 2) - max_num
            else:
                # Convert binary string to decimal integer
                return int(binary_str, 2)
        else:
            return None
        
    @staticmethod
    def hex(binary_str):
        if binary_str is not None:
            return hex(Instruction.decimal(binary_str))
        else:
            return None

    def process(self):
        self.sanitize_input()
        self.extract_opcode()
        self.extract_rs1()
        self.determine_type()
        self.extract_rs2()
        self.extract_rd()
        self.extract_funct3()
        self.extract_ins30()
        self.extract_funct7()
        self.extract_imm()
        self.determine_function()

if __name__ == '__main__':
    # Get input from user
    input_str = input('Enter an instruction word: ')
    #input_str = "0000 0000 0100 0001 1000 1100 0110 0011"

    # If you know what your registers are assigned
    # Input them here, and rs1, rs2, and rd values can be auto-calculated.
    registers = {
        0:0
    }

    from tabulate import tabulate
    # Create Instruction object and process input
    instr = Instruction(input_str)
    instr.process()

    # Create a list of tuples representing the rows of the table
    table_data = [
        ('Input', instr.sanitized_str, '-', '-', Instruction.hex(instr.sanitized_str)),
        ('Opcode', instr.opcode, '-', '-', instr.type),
        ('RS1', instr.rs1, Instruction.decimal(instr.rs1), registers.get(Instruction.decimal(instr.rs1), 'Unknown'), '-'),
        ('RS2', instr.rs2, Instruction.decimal(instr.rs2), registers.get(Instruction.decimal(instr.rs2), 'Unknown'), '-'),
        ('RD', instr.rd, Instruction.decimal(instr.rd), registers.get(Instruction.decimal(instr.rd), 'Unknown'), '-'),
        ('INS30', instr.ins30, '-', '-', '-'),
        ('FUNCT3', instr.funct3, '-', '-', instr.function),
        ('FUNCT7', instr.funct7, '-', '-', Instruction.decimal(instr.funct7)),
        ('IMM', instr.imm, '-', '-', Instruction.decimal(instr.imm)),
    ]

    # Use tabulate to format the table
    table = tabulate(table_data, headers=['Field', 'Value', 'Register #', 'Value in Register', 'Info'], tablefmt='grid', colalign=('left', 'left', 'left', 'left', 'left'))

    # Print the table
    print(table)